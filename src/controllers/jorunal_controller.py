from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.journal_service import JournalService

journal_bp = Blueprint("journal", __name__, url_prefix="/api/journals")


def extract_user_id():
    """
    Extract the google_id from the JWT payload.
    """
    return get_jwt_identity()["google_id"]


@journal_bp.route("", methods=["POST"])
@jwt_required()
def create_journal_entry():
    user_id = extract_user_id()
    data = request.json
    if not data or "entry" not in data:
        return jsonify({"error": "Entry content is required"}), 400

    try:
        request_ip = request.remote_addr
        entry_id = JournalService.create_journal_entry(user_id, data["entry"], request_ip)
        return jsonify({"message": "Journal entry created successfully", "entry_id": entry_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@journal_bp.route("", methods=["GET"])
@jwt_required()
def get_all_journal_entries():
    user_id = extract_user_id()
    try:
        journal_entries = JournalService.get_all_journal_entries(user_id)
        if not journal_entries:
            return jsonify({"message": "No journal entries found"}), 404
        return jsonify({"message": "Journal entries retrieved", "entries": journal_entries}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@journal_bp.route("/<entry_id>", methods=["DELETE"])
@jwt_required()
def delete_journal_entry(entry_id):
    user_id = extract_user_id()
    try:
        success = JournalService.delete_journal_entry(entry_id)
        if not success:
            return jsonify({"error": "Journal entry not found"}), 404
        return jsonify({"message": "Journal entry deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@journal_bp.route("/recent", methods=["GET"])
@jwt_required()
def get_recent_entries():
    user_id = extract_user_id()
    try:
        entries = JournalService.get_recent_entries(user_id)
        return jsonify(entries), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@journal_bp.route("/filter", methods=["GET"])
@jwt_required()
def get_entries_by_time():
    user_id = extract_user_id()
    year = request.args.get("year")
    month = request.args.get("month")
    if not year or not month:
        return jsonify({"error": "Both 'year' and 'month' parameters are required."}), 400
    try:
        entries = JournalService.get_entries_by_month(user_id, year, month)
        return jsonify(entries), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@journal_bp.route("/heatmap", methods=["GET"])
@jwt_required()
def get_heatmap_data():
    user_id = extract_user_id()
    try:
        heatmap_data = JournalService.get_heatmap_data(user_id)
        return jsonify(heatmap_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@journal_bp.route("/dashboard/sentiments", methods=["GET"])
@jwt_required()
def get_dashboard_sentiments():
    user_id = extract_user_id()
    try:
        sentiments = JournalService.get_dashboard_sentiments(user_id)
        return jsonify(sentiments), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@journal_bp.route("/search", methods=["GET"])
@jwt_required()
def get_entries_by_keyword():
    """
    Retrieve all journal entries for a user that contain a specific keyword.
    Example: GET /api/journals/search?keyword=workout
    """
    user_id = extract_user_id()
    keyword = request.args.get("keyword")
    if not keyword:
        return jsonify({"error": "Keyword parameter is required"}), 400

    try:
        entries = JournalService.get_entries_by_keyword(user_id, keyword)
        return jsonify({"message": f"Entries with keyword '{keyword}' retrieved", "entries": entries}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@journal_bp.route("/keywords/top", methods=["GET"])
@jwt_required()
def get_top_keywords():
    """
    Retrieve the top N most common keywords for a user.
    Example: GET /api/journals/keywords/top?top_n=5
    """
    user_id = extract_user_id()
    top_n = request.args.get("top_n", default=10, type=int)

    try:
        keywords = JournalService.get_top_keywords(user_id, top_n)
        return jsonify({"message": f"Top {top_n} keywords retrieved", "keywords": keywords}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500