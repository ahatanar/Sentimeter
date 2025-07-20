from typing import Dict, Any, Optional, List
from datetime import datetime, time, timezone
from src.models.notification_model import NotificationSettings
from src.models.user_model import User
from src.services.email_service import EmailService
import random


class NotificationService:
    """Service for managing notification settings and sending emails"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.journal_prompts = [
            "Write about the most challenging moment of your day and how you handled it.",
            "Reflect on something that made you smile today, no matter how small.",
            "Describe a conversation that stuck with you today and why it was meaningful.",
            "What's something you're grateful for right now?",
            "Write about a goal you're working toward and your progress so far.",
            "Describe a moment today when you felt proud of yourself.",
            "What's something you're looking forward to tomorrow?",
            "Reflect on a decision you made today and how it turned out.",
            "Write about someone who made a positive impact on your day.",
            "What's something you learned about yourself today?"
        ]
    
    def get_user_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get notification settings for a user"""
        settings = NotificationSettings.find_by_user_id(user_id)
        if not settings:
            return None
        
        return {
            "journal_enabled": settings.journal_enabled,
            "journal_frequency": settings.journal_frequency,
            "journal_day": settings.journal_day,
            "journal_time": settings.journal_time.strftime("%H:%M") if settings.journal_time else "20:00",
            "survey_enabled": settings.survey_enabled,
            "survey_day": settings.survey_day,
            "survey_time": settings.survey_time.strftime("%H:%M") if settings.survey_time else "18:00",
            "created_at": settings.created_at.isoformat() if settings.created_at else None,
            "updated_at": settings.updated_at.isoformat() if settings.updated_at else None
        }
    
    def update_user_settings(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Update notification settings for a user"""
        # Validate input
        valid_fields = [
            "journal_enabled", "journal_frequency", "journal_time", "journal_day",
            "survey_enabled", "survey_day", "survey_time"
        ]
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        # Convert time string to time object if provided
        if "journal_time" in filtered_kwargs and isinstance(filtered_kwargs["journal_time"], str):
            try:
                time_obj = datetime.strptime(filtered_kwargs["journal_time"], "%H:%M").time()
                filtered_kwargs["journal_time"] = time_obj
            except ValueError:
                raise ValueError("journal_time must be in HH:MM format")
        
        # Convert survey time string to time object if provided
        if "survey_time" in filtered_kwargs and isinstance(filtered_kwargs["survey_time"], str):
            try:
                time_obj = datetime.strptime(filtered_kwargs["survey_time"], "%H:%M").time()
                filtered_kwargs["survey_time"] = time_obj
            except ValueError:
                raise ValueError("survey_time must be in HH:MM format")
        
        # Update settings
        settings = NotificationSettings.update_settings(user_id, **filtered_kwargs)
        
        return self.get_user_settings(user_id)
    
    def create_default_settings(self, user_id: str) -> Dict[str, Any]:
        """Create default notification settings for a new user"""
        settings = NotificationSettings.create_default_settings(user_id)
        return self.get_user_settings(user_id)
    
    def send_journal_reminder(self, user_id: str) -> bool:
        """Send a journal reminder email to a user"""
        user = User.find_by_google_id(user_id)
        if not user:
            return False
        
        settings = NotificationSettings.find_by_user_id(user_id)
        if not settings or not settings.journal_enabled:
            return False
        
        # Get a random journal prompt
        prompt = random.choice(self.journal_prompts)
        
        # Send the email
        return self.email_service.send_journal_reminder(user.email, user.name, prompt)
    
    def send_test_email(self, user_id: str) -> bool:
        """Send a test email to a user"""
        user = User.find_by_google_id(user_id)
        if not user:
            return False
        
        # Send the test email
        return self.email_service.send_test_email(user.email, user.name)
    
    def get_users_for_journal_reminder(self, current_time: time, current_weekday: str = None) -> List[str]:
        """Get list of user IDs who should receive journal reminders at the given time"""
        # Convert current time to UTC for consistent comparison
        utc_now = datetime.now(timezone.utc)
        current_utc_time = utc_now.time()
        
        # Base query for enabled notifications at current time
        query = NotificationSettings.query.filter(
            NotificationSettings.journal_enabled == True,
            NotificationSettings.journal_time == current_utc_time
        )
        
        # Add weekday filter if provided
        if current_weekday:
            query = query.filter(NotificationSettings.journal_day == current_weekday)
        
        settings = query.all()
        return [setting.user_id for setting in settings]
    
    def get_journal_prompts(self) -> List[str]:
        """Get all available journal prompts"""
        return self.journal_prompts.copy() 