from flask import Blueprint, request, jsonify
from src.services.journal_service import JournalService

journal_bp = Blueprint("journal", __name__, url_prefix="/api/journals")

# POST /api/journals
@journal_bp.route("", methods=["POST"])
def create_journal_entry():
    """
    Create a new journal entry for the user.
    Expects: JSON with "user_id" and "entry".
    """
    data = request.json

    # Validate input
    if not data or "user_id" not in data or "entry" not in data:
        return jsonify({"error": "User ID and entry are required"}), 400

    try:
        # Delegate to the JournalService
        entry_id = JournalService.create_journal_entry(data["user_id"], data["entry"])
        return jsonify({"message": "Journal entry created successfully", "entry_id": entry_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# GET /api/journals/<user_id>
@journal_bp.route("/<user_id>", methods=["GET"])
def get_all_journal_entries(user_id):
    """
    Retrieve all journal entries for a user.
    """
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
def delete_journal_entry(entry_id):
    """
    Delete a specific journal entry by entry ID.
    """
    try:
        # Delegate to the JournalService
        success = JournalService.delete_journal_entry(entry_id)

        if not success:
            return jsonify({"error": "Journal entry not found"}), 404

        return jsonify({"message": "Journal entry deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
