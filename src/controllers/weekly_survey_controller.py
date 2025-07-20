from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.weekly_survey_service import WeeklySurveyService

weekly_survey_bp = Blueprint("weekly_survey", __name__, url_prefix="/api/weekly-surveys")


def extract_user_id():
    """
    Extract the `google_id` from the JWT payload.
    
    :return: The `google_id` of the authenticated user.
    """
    identity = get_jwt_identity()
    return identity


@weekly_survey_bp.route("", methods=["POST"])
@jwt_required()
def create_weekly_survey():
    """
    Create a new weekly survey for the authenticated user.
    
    Endpoint: POST /api/weekly-surveys
    
    Request Body:
    {
        "stress": 3,
        "anxiety": 2,
        "depression": 1,
        "happiness": 4,
        "satisfaction": 4,
        "self_harm_thoughts": false,
        "significant_sleep_issues": false,
        "week_start": "2024-01-01"  # Optional: ISO date for specific week
    }
    
    :return: JSON response with status and urgent flag.
    """
    user_id = extract_user_id()
    data = request.json

    if not data:
        return jsonify({"error": "Survey data is required"}), 400

    try:
        result = WeeklySurveyService.create_weekly_survey(user_id, data)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Failed to create survey"}), 500


@weekly_survey_bp.route("", methods=["GET"])
@jwt_required()
def get_weekly_surveys():
    """
    Retrieve weekly surveys for the authenticated user.
    
    Endpoint: GET /api/weekly-surveys
    
    Query Parameters:
    - range: "last12" (default) - get last 12 weeks
    - since: "YYYY-MM-DD" - get surveys since specific date
    
    :return: JSON response with list of surveys.
    """
    user_id = extract_user_id()
    
    # Get query parameters
    range_type = request.args.get("range", "last12")
    since_date = request.args.get("since")
    
    try:
        surveys = WeeklySurveyService.get_user_surveys(user_id, range_type, since_date)
        return jsonify({"surveys": surveys}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Failed to retrieve surveys"}), 500


@weekly_survey_bp.route("/check", methods=["GET"])
@jwt_required()
def check_survey_exists():
    """
    Check if user has already completed a survey this week.
    
    Endpoint: GET /api/weekly-surveys/check
    
    :return: JSON response indicating if survey exists this week.
    """
    user_id = extract_user_id()
    
    try:
        exists = WeeklySurveyService.check_survey_exists_this_week(user_id)
        return jsonify({"survey_exists_this_week": exists}), 200
    except Exception as e:
        return jsonify({"error": "Failed to check survey status"}), 500


@weekly_survey_bp.route("/missing-weeks", methods=["GET"])
@jwt_required()
def get_missing_weeks():
    """
    Get list of missing weeks for the user (for week picker).
    
    Endpoint: GET /api/weekly-surveys/missing-weeks
    
    :return: JSON response with list of missing week dates.
    """
    user_id = extract_user_id()
    
    try:
        missing_weeks = WeeklySurveyService.get_missing_weeks(user_id)
        return jsonify({"missing_weeks": missing_weeks}), 200
    except Exception as e:
        return jsonify({"error": "Failed to get missing weeks"}), 500


@weekly_survey_bp.route("/test-reminder", methods=["POST"])
@jwt_required()
def test_survey_reminder():
    """
    Test endpoint to manually trigger a survey reminder email.
    
    Endpoint: POST /api/weekly-surveys/test-reminder
    
    :return: JSON response indicating if email was sent successfully.
    """
    user_id = extract_user_id()
    
    try:
        from src.services.survey_scheduler import send_survey_reminder_task
        
        # Trigger the task synchronously for testing
        result = send_survey_reminder_task(user_id)
        
        if result.get("success"):
            return jsonify({
                "message": "Survey reminder sent successfully",
                "user_name": result.get("user_name")
            }), 200
        else:
            return jsonify({
                "error": result.get("error", "Failed to send reminder")
            }), 400
            
    except Exception as e:
        return jsonify({"error": f"Failed to send test reminder: {str(e)}"}), 500 