from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.journal_service import JournalService

journal_bp = Blueprint("journal", __name__, url_prefix="/api/journals")


def extract_user_id():
    """
    Extract the `google_id` from the JWT payload.
    
    :return: The `google_id` of the authenticated user.
    """
    return get_jwt_identity()["google_id"]


def get_client_ip():
    """
    Get the real client IP address from the 'X-Forwarded-For' header.
    """
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # X-Forwarded-For can have multiple IPs, separated by commas; take the first one
        return x_forwarded_for.split(",")[0].strip()
    return request.remote_addr
@journal_bp.route("", methods=["POST"])
@jwt_required()
def create_journal_entry():
    """
    Create a new journal entry for the authenticated user.
    
    Endpoint: POST /api/journals
    
    Request Body:
    {
        "entry": "Your journal entry text",
        "date": "Optional date in ISO format (e.g., 2024-11-30T14:30:00)",
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060
        }  # Optional
    }
    
    :return: JSON response with a success message and the `entry_id` if created successfully.
    """
    user_id = extract_user_id()
    data = request.json

    if not data or "entry" not in data:
        return jsonify({"error": "Entry content is required"}), 400

    try:
        client_ip = get_client_ip()  
        location_data = data.get("location")  
        optional_date = data.get("date")
        entry = JournalService.create_journal_entry(
            user_id, data["entry"], client_ip, optional_date, location_data
        )
        return jsonify({"message": "Journal entry created successfully", "entry": entry}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@journal_bp.route("", methods=["GET"])
@jwt_required()
def get_all_journal_entries():
    """
    Retrieve all journal entries for the authenticated user.
    
    Endpoint: GET /api/journals
    
    :return: JSON response with a list of all journal entries or a 404 message if none found.
    """
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
    """
    Delete a specific journal entry by its `entry_id`.
    
    Endpoint: DELETE /api/journals/<entry_id>
    
    :param entry_id: The ID of the journal entry to delete.
    :return: JSON response with a success or error message.
    """
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
    """
    Retrieve the most recent journal entries for the authenticated user.
    
    Endpoint: GET /api/journals/recent
    
    :return: JSON response with the most recent journal entries.
    """
    user_id = extract_user_id()
    try:
        entries = JournalService.get_recent_entries(user_id)
        return jsonify(entries), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@journal_bp.route("/filter", methods=["GET"])
@jwt_required()
def get_entries_by_time():
    """
    Retrieve journal entries for a specific year and month.
    
    Endpoint: GET /api/journals/filter?year=<year>&month=<month>
    
    Query Parameters:
    - `year`: The year to filter journal entries (e.g., 2024).
    - `month`: The month to filter journal entries (e.g., 11 for November).
    
    :return: JSON response with the filtered journal entries or an error message.
    """
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
    """
    Retrieve heatmap data for the authenticated user's journal entries.
    
    Endpoint: GET /api/journals/heatmap
    
    :return: JSON response with heatmap data.
    """
    user_id = extract_user_id()
    try:
        heatmap_data = JournalService.get_heatmap_data(user_id)
        return jsonify(heatmap_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@journal_bp.route("/sentiments", methods=["GET"])
@jwt_required()
def get_dashboard_sentiments():
    """
    Retrieve sentiment analysis data for the authenticated user's dashboard.
    
    Endpoint: GET /api/journals/dashboard/sentiments
    
    :return: JSON response with sentiment data for the dashboard.
    """
    user_id = extract_user_id()
    try:
        sentiments = JournalService.get_dashboard_sentiments(user_id)
        return jsonify(sentiments), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@journal_bp.route("/keywords", methods=["GET"])
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
    

@journal_bp.route("/search/keyword", methods=["GET"])
@jwt_required()
def get_entries_by_keyword():
    """
    Retrieve journal entries by keyword for a specific user.

    Endpoint: GET /api/journals/entries/keyword?keyword=<keyword>
    :query_param keyword: The keyword to filter entries by.
    :return: JSON response containing the matching journal entries.
    """
    user_id = extract_user_id()
    keyword = request.args.get("keyword")

    if not keyword:
        return jsonify({"error": "Keyword parameter is required."}), 400

    try:
        entries = JournalService.get_entries_by_keyword(user_id, keyword)
        return jsonify({"entries": entries}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@journal_bp.route("/search/date", methods=["GET"])
@jwt_required()
def get_entries_by_month():
    """
    Retrieve journal entries for a specific month and year.

    Endpoint: GET /api/journals/entries/month?year=<year>&month=<month>
    :query_param year: The year to filter by.
    :query_param month: The month to filter by.
    :return: JSON response containing the journal entries for the given month and year.
    """
    user_id = extract_user_id()
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    if not year or not month:
        return jsonify({"error": "Year and month parameters are required."}), 400

    try:
        entries = JournalService.get_entries_by_month(user_id, year, month)
        return jsonify({"entries": entries}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
