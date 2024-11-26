from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.journal_service import JournalService

journal_bp = Blueprint("journal", __name__, url_prefix="/api/journals")


# POST /api/journals
@journal_bp.route("", methods=["POST"])
@jwt_required()
def create_journal_entry():
    """
    Create a new journal entry for the user.
    Expects: JSON with "entry".
    """
    user_id = get_jwt_identity()  # Extract user ID from JWT
    data = request.json

    # Validate input
    if not data or "entry" not in data:
        return jsonify({"error": "Entry content is required"}), 400

    try:
        # Delegate to the JournalService
        entry_id = JournalService.create_journal_entry(user_id, data["entry"])
        return jsonify({"message": "Journal entry created successfully", "entry_id": entry_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# GET /api/journals
@journal_bp.route("", methods=["GET"])
@jwt_required()
def get_all_journal_entries():
    """
    Retrieve all journal entries for the current user.
    """
    user_id = get_jwt_identity()  # Extract user ID from JWT

    try:
        # Delegate to the JournalService
        journal_entries = JournalService.get_all_journal_entries(user_id)

        if not journal_entries:
            return jsonify({"message": "No journal entries found"}), 404

        return jsonify({"message": "Journal entries retrieved", "entries": journal_entries}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# DELETE /api/journals/<entry_id>
@journal_bp.route("/<entry_id>", methods=["DELETE"])
@jwt_required()
def delete_journal_entry(entry_id):
    """
    Delete a specific journal entry by entry ID.
    """
    user_id = get_jwt_identity()  # Extract user ID from JWT

    try:
        # Delegate to the JournalService
        success = JournalService.delete_journal_entry(user_id, entry_id)

        if not success:
            return jsonify({"error": "Journal entry not found"}), 404

        return jsonify({"message": "Journal entry deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@journal_bp.route("/recent", methods=["GET"])
@jwt_required()
def get_recent_entries():
    """
    Fetch the last 10 journal entries for the logged-in user.
    """
    user_id = get_jwt_identity()  # Extract user ID from JWT
    try:
        entries = JournalService.get_recent_entries(user_id)
        return jsonify(entries), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@journal_bp.route("/filter", methods=["GET"])
@jwt_required()
def get_entries_by_time():
    """
    Fetch journal entries filtered by year and month.
    Example usage:
        /api/journals/filter?year=2024&month=11
    """
    user_id = get_jwt_identity()  # Extract user ID from JWT
    year = request.args.get("year")
    month = request.args.get("month")

    if not year or not month:
        return jsonify({"error": "Both 'year' and 'month' parameters are required."}), 400

    try:
        entries = JournalService.get_entries_by_month(user_id, year, month)
        return jsonify(entries), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
