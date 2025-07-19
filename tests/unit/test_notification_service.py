import pytest
from unittest.mock import Mock, patch
from datetime import datetime, time
from src.services.notification_service import NotificationService
from src.models.notification_model import NotificationSettings
from src.models.user_model import User


class TestNotificationService:
    
    @pytest.fixture
    def notification_service(self):
        return NotificationService()
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.user_id = "test_user_id"
        user.email = "test@example.com"
        user.name = "Test User"
        return user
    
    @pytest.fixture
    def mock_settings(self):
        settings = Mock(spec=NotificationSettings)
        settings.user_id = "test_user_id"
        settings.journal_enabled = True
        settings.journal_frequency = "daily"
        settings.journal_time = time(20, 0)  # 8 PM
        settings.created_at = datetime.now()
        settings.updated_at = datetime.now()
        return settings
    
    def test_get_journal_prompts(self, notification_service):
        """Test that journal prompts are returned"""
        prompts = notification_service.get_journal_prompts()
        assert isinstance(prompts, list)
        assert len(prompts) > 0
        assert all(isinstance(prompt, str) for prompt in prompts)
    
    @patch('src.services.notification_service.User.find_by_google_id')
    @patch('src.services.notification_service.NotificationSettings.find_by_user_id')
    @patch('src.services.notification_service.EmailService.send_journal_reminder')
    def test_send_journal_reminder_success(self, mock_send_email, mock_find_settings, mock_find_user, 
                                         notification_service, mock_user, mock_settings):
        """Test successful journal reminder sending"""
        mock_find_user.return_value = mock_user
        mock_find_settings.return_value = mock_settings
        mock_send_email.return_value = True
        
        result = notification_service.send_journal_reminder("test_user_id")
        
        assert result is True
        mock_send_email.assert_called_once()
    
    @patch('src.services.notification_service.User.find_by_google_id')
    def test_send_journal_reminder_user_not_found(self, mock_find_user, notification_service):
        """Test journal reminder when user not found"""
        mock_find_user.return_value = None
        
        result = notification_service.send_journal_reminder("invalid_user_id")
        
        assert result is False
    
    @patch('src.services.notification_service.User.find_by_google_id')
    @patch('src.services.notification_service.NotificationSettings.find_by_user_id')
    def test_send_journal_reminder_notifications_disabled(self, mock_find_settings, mock_find_user,
                                                        notification_service, mock_user):
        """Test journal reminder when notifications are disabled"""
        mock_find_user.return_value = mock_user
        mock_settings = Mock()
        mock_settings.journal_enabled = False
        mock_find_settings.return_value = mock_settings
        
        result = notification_service.send_journal_reminder("test_user_id")
        
        assert result is False
    
    @patch('src.services.notification_service.User.find_by_google_id')
    @patch('src.services.notification_service.EmailService.send_test_email')
    def test_send_test_email_success(self, mock_send_email, mock_find_user, 
                                   notification_service, mock_user):
        """Test successful test email sending"""
        mock_find_user.return_value = mock_user
        mock_send_email.return_value = True
        
        result = notification_service.send_test_email("test_user_id")
        
        assert result is True
        mock_send_email.assert_called_once()
    
    @patch('src.services.notification_service.User.find_by_google_id')
    def test_send_test_email_user_not_found(self, mock_find_user, notification_service):
        """Test test email when user not found"""
        mock_find_user.return_value = None
        
        result = notification_service.send_test_email("invalid_user_id")
        
        assert result is False 