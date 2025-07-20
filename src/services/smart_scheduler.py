"""
Smart scheduler for email notifications that only runs at common reminder times.
This is much more efficient than running every minute.
"""

from celery import Celery
from datetime import datetime, time
from src.services.notification_service import NotificationService
import os

# Initialize Celery
celery_app = Celery('sentimeter')

# Configure Celery
celery_app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

notification_service = NotificationService()

# Check every 15 minutes for more precise timing
CHECK_INTERVAL_MINUTES = 15


@celery_app.task
def send_bulk_journal_reminders():
    """Smart task that runs every 15 minutes to check for reminders"""
    try:
        current_time = datetime.now().time()
        current_weekday = datetime.now().strftime("%A").lower()
        
        # Get users who need reminders now
        user_ids = notification_service.get_users_for_journal_reminder(current_time, current_weekday)
        
        results = []
        for user_id in user_ids:
            result = send_journal_reminder_task.delay(user_id)
            results.append(result)
        
        return {
            "success": True,
            "users_scheduled": len(user_ids),
            "check_time": current_time.strftime("%H:%M"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        current_time = datetime.now().time()
        current_weekday = datetime.now().strftime("%A").lower()
        
        # Get users who need reminders now
        user_ids = notification_service.get_users_for_journal_reminder(current_time, current_weekday)
        
        results = []
        for user_id in user_ids:
            result = send_journal_reminder_task.delay(user_id)
            results.append(result)
        
        return {
            "success": True,
            "users_scheduled": len(user_ids),
            "reminder_hour": current_hour,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task
def send_journal_reminder_task(user_id: str):
    """Celery task to send a journal reminder email"""
    try:
        success = notification_service.send_journal_reminder(user_id)
        return {
            "success": success,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }


def schedule_user_reminders(user_id: str, settings: dict):
    """Schedule reminders for a user when they update settings"""
    if not settings.get("journal_enabled"):
        return None
    
    frequency = settings.get("journal_frequency", "daily")
    time_str = settings.get("journal_time", "20:00")
    day = settings.get("journal_day", "monday")
    
    # Parse time
    hour, minute = map(int, time_str.split(":"))
    
    # Schedule the reminder
    task = send_journal_reminder_task.apply_async(
        args=[user_id],
        eta=datetime.combine(datetime.now().date(), time(hour, minute))
    )
    return task.id


# Celery Beat Schedule (runs every 15 minutes)
celery_app.conf.beat_schedule = {
    'send-journal-reminders': {
        'task': 'src.services.smart_scheduler.send_bulk_journal_reminders',
        'schedule': 900.0,  # Every 15 minutes (15 * 60 seconds)
    },
} 