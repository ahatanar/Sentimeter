from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.notification_service import NotificationService
from src.models.user_model import User

notification_bp = Blueprint('notification', __name__, url_prefix='/api/notifications')
notification_service = NotificationService()


@notification_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_notification_settings():
    """Get user's notification settings"""
    try:
        user_id = get_jwt_identity()
        
        # Check if user exists
        user = User.find_by_google_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get settings
        settings = notification_service.get_user_settings(user_id)
        
        if settings is None:
            # Create default settings if none exist
            settings = notification_service.create_default_settings(user_id)
        
        return jsonify({
            "success": True,
            "settings": settings
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@notification_bp.route('/settings', methods=['POST'])
@jwt_required()
def update_notification_settings():
    """Update user's notification settings"""
    try:
        user_id = get_jwt_identity()
        
        # Check if user exists
        user = User.find_by_google_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        allowed_fields = ["journal_enabled", "journal_frequency", "journal_time"]
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify({"error": "No valid fields provided"}), 400
        
        # Validate journal_frequency
        if "journal_frequency" in update_data:
            if update_data["journal_frequency"] not in ["daily", "weekly"]:
                return jsonify({"error": "journal_frequency must be 'daily' or 'weekly'"}), 400
        
        # Validate journal_time format
        if "journal_time" in update_data:
            try:
                from datetime import datetime
                datetime.strptime(update_data["journal_time"], "%H:%M")
            except ValueError:
                return jsonify({"error": "journal_time must be in HH:MM format"}), 400
        
        # Update settings
        updated_settings = notification_service.update_user_settings(user_id, **update_data)
        
        return jsonify({
            "success": True,
            "message": "Notification settings updated successfully",
            "settings": updated_settings
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@notification_bp.route('/test', methods=['POST'])
@jwt_required()
def send_test_email():
    """Send a test email to the user"""
    try:
        user_id = get_jwt_identity()
        
        # Check if user exists
        user = User.find_by_google_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Send test email
        success = notification_service.send_test_email(user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Test email sent successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Failed to send test email"
            }), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@notification_bp.route('/prompts', methods=['GET'])
@jwt_required()
def get_journal_prompts():
    """Get all available journal prompts"""
    try:
        prompts = notification_service.get_journal_prompts()
        
        return jsonify({
            "success": True,
            "prompts": prompts
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 