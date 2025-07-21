"""
Survey scheduler for weekly survey reminders.
This runs daily and sends reminders to users who haven't completed their survey for the current week.
"""

from celery import Celery
from datetime import datetime, timedelta
from src.services.notification_service import NotificationService
from src.services.weekly_survey_service import WeeklySurveyService
from src.models.user_model import User
from src.models.notification_model import NotificationSettings
from src.services.email_service import EmailService
import os

# Initialize Celery (reuse existing config)
from src.services.smart_scheduler import celery_app

# Initialize services
notification_service = NotificationService()
email_service = EmailService()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@celery_app.task
def send_weekly_survey_reminders():
    """Send weekly survey reminders to users who haven't completed this week's survey"""
    try:
        today = datetime.utcnow().date()
        weekday = today.strftime("%A").lower()  # e.g. 'sunday'
        week_start = WeeklySurveyService.calculate_week_start()
        
        # Get users who should receive survey reminders today
        users_to_remind = get_users_for_survey_reminder(weekday)
        
        results = []
        for user in users_to_remind:
            # Check if user already completed survey this week
            survey_exists = WeeklySurveyService.check_survey_exists_this_week(user.user_id)
            
            if not survey_exists:
                result = send_survey_reminder_task.delay(user.user_id)
                results.append(result)
            else:
                pass
        
        return {
            "success": True,
            "users_scheduled": len(results),
            "check_time": datetime.utcnow().strftime("%H:%M"),
            "weekday": weekday,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"❌ [SURVEY_SCHEDULER] Error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task
def send_survey_reminder_task(user_id: str):
    """Send a survey reminder email to a specific user"""
    try:
        user = User.find_by_google_id(user_id)
        if not user:
            print(f"❌ [SURVEY_REMINDER] User not found: {user_id}")
            return {"success": False, "error": "User not found", "user_id": user_id}
        
        settings = NotificationSettings.find_by_user_id(user_id)
        if not settings or not settings.survey_enabled:
            print(f"⏭️ [SURVEY_REMINDER] Survey notifications disabled for user: {user.name}")
            return {"success": False, "error": "Survey notifications disabled", "user_id": user_id}
        
        # Generate survey link
        survey_link = f"{FRONTEND_URL}/weekly-checkin"
        
        # Send the email
        success = email_service.send_weekly_survey_reminder(
            user.email, 
            user.name, 
            survey_link
        )
        
        if success:
            print(f"✅ [SURVEY_REMINDER] Email sent successfully to: {user.name}")
            return {
                "success": True,
                "user_id": user_id,
                "user_name": user.name,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            print(f"❌ [SURVEY_REMINDER] Failed to send email to: {user.name}")
            return {
                "success": False,
                "error": "Email sending failed",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        print(f"❌ [SURVEY_REMINDER] Error sending reminder to {user_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }


def get_users_for_survey_reminder(weekday: str) -> list:
    """Get list of users who should receive survey reminders on the given weekday"""
    try:
        # Query users with survey notifications enabled for the specific weekday
        users = (
            User.query
            .join(NotificationSettings)
            .filter(NotificationSettings.survey_enabled.is_(True))
            .filter(NotificationSettings.survey_day == weekday)
            .all()
        )
        
        print(f"🔍 [SURVEY_SCHEDULER] Found {len(users)} users with survey notifications on {weekday}")
        return users
        
    except Exception as e:
        print(f"❌ [SURVEY_SCHEDULER] Error getting users: {str(e)}")
        return []


# Register the task in the existing beat schedule
# This will be added to the existing smart_scheduler.py beat_schedule 