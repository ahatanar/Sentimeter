import pytest
from unittest.mock import patch, MagicMock
from datetime import date, datetime
from src.services.survey_scheduler import get_users_for_survey_reminder, send_survey_reminder_task
from src.services.weekly_survey_service import WeeklySurveyService


class TestSurveyScheduler:
    """Test survey scheduler functionality"""
    
    @patch('src.services.survey_scheduler.User')
    @patch('src.services.survey_scheduler.NotificationSettings')
    def test_get_users_for_survey_reminder(self, mock_notification_settings, mock_user):
        """Test getting users for survey reminders"""
        # Mock user and settings
        mock_user_instance = MagicMock()
        mock_user_instance.user_id = "test_user"
        mock_user_instance.name = "Test User"
        
        mock_settings_instance = MagicMock()
        mock_settings_instance.survey_enabled = True
        mock_settings_instance.survey_day = "sunday"
        
        # Mock the query
        mock_query = MagicMock()
        mock_query.join.return_value.filter.return_value.filter.return_value.all.return_value = [mock_user_instance]
        mock_user.query = mock_query
        
        users = get_users_for_survey_reminder("sunday")
        
        assert len(users) == 1
        assert users[0].user_id == "test_user"
        assert users[0].name == "Test User"
    
    @patch('src.services.survey_scheduler.User')
    @patch('src.services.survey_scheduler.NotificationSettings')
    @patch('src.services.survey_scheduler.email_service')
    @patch('src.services.survey_scheduler.WeeklySurveyService')
    def test_send_survey_reminder_task_success(self, mock_weekly_survey, mock_email_service, mock_notification_settings, mock_user):
        """Test successful survey reminder email"""
        # Mock user
        mock_user_instance = MagicMock()
        mock_user_instance.user_id = "test_user"
        mock_user_instance.name = "Test User"
        mock_user_instance.email = "test@example.com"
        mock_user.find_by_google_id.return_value = mock_user_instance
        
        # Mock settings
        mock_settings_instance = MagicMock()
        mock_settings_instance.survey_enabled = True
        mock_notification_settings.find_by_user_id.return_value = mock_settings_instance
        
        # Mock email service
        mock_email_service.send_weekly_survey_reminder.return_value = True
        
        # Mock survey check
        mock_weekly_survey.check_survey_exists_this_week.return_value = False
        
        result = send_survey_reminder_task("test_user")
        
        assert result["success"] is True
        assert result["user_id"] == "test_user"
        assert result["user_name"] == "Test User"
        mock_email_service.send_weekly_survey_reminder.assert_called_once()
    
    @patch('src.services.survey_scheduler.User')
    def test_send_survey_reminder_task_user_not_found(self, mock_user):
        """Test survey reminder when user not found"""
        mock_user.find_by_google_id.return_value = None
        
        result = send_survey_reminder_task("nonexistent_user")
        
        assert result["success"] is False
        assert "User not found" in result["error"]
    
    @patch('src.services.survey_scheduler.User')
    @patch('src.services.survey_scheduler.NotificationSettings')
    def test_send_survey_reminder_task_notifications_disabled(self, mock_notification_settings, mock_user):
        """Test survey reminder when notifications are disabled"""
        # Mock user
        mock_user_instance = MagicMock()
        mock_user_instance.user_id = "test_user"
        mock_user_instance.name = "Test User"
        mock_user.find_by_google_id.return_value = mock_user_instance
        
        # Mock settings with notifications disabled
        mock_settings_instance = MagicMock()
        mock_settings_instance.survey_enabled = False
        mock_notification_settings.find_by_user_id.return_value = mock_settings_instance
        
        result = send_survey_reminder_task("test_user")
        
        assert result["success"] is False
        assert "Survey notifications disabled" in result["error"] 