import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from src.controllers.notification_controller import notification_bp


class TestNotificationController(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        self.app.config['TESTING'] = True
        self.app.register_blueprint(notification_bp)
        self.jwt = JWTManager(self.app)
        self.client = self.app.test_client()

        # Push the application context
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()
        patch.stopall()

    def get_jwt_headers(self, user_id):
        access_token = create_access_token(identity=user_id)
        return {'Authorization': f'Bearer {access_token}'}

    def test_get_notification_settings_unauthorized(self):
        """Test GET /api/notifications/settings without authentication"""
        response = self.client.get('/api/notifications/settings')
        self.assertEqual(response.status_code, 401)

    @patch('src.models.user_model.User.find_by_google_id')
    @patch('src.services.notification_service.NotificationService.get_user_settings')
    def test_get_notification_settings_success(self, mock_get_settings, mock_find_user):
        """Test GET /api/notifications/settings with authentication"""
        mock_find_user.return_value = MagicMock(user_id='test_user', email='test@example.com', name='Test User')
        mock_get_settings.return_value = {
            "journal_enabled": False,
            "journal_frequency": "daily",
            "journal_time": "20:00",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        headers = self.get_jwt_headers('test_user')
        response = self.client.get('/api/notifications/settings', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('settings', data)
        self.assertIn('journal_enabled', data['settings'])
        self.assertIn('journal_frequency', data['settings'])
        self.assertIn('journal_time', data['settings'])

    @patch('src.models.user_model.User.find_by_google_id')
    @patch('src.services.notification_service.NotificationService.update_user_settings')
    def test_post_notification_settings_success(self, mock_update_settings, mock_find_user):
        """Test POST /api/notifications/settings with valid data"""
        mock_find_user.return_value = MagicMock(user_id='test_user', email='test@example.com', name='Test User')
        mock_update_settings.return_value = {
            "journal_enabled": True,
            "journal_frequency": "daily",
            "journal_time": "21:00",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        update_data = {
            "journal_enabled": True,
            "journal_frequency": "daily",
            "journal_time": "21:00"
        }
        
        headers = self.get_jwt_headers('test_user')
        headers['Content-Type'] = 'application/json'
        response = self.client.post('/api/notifications/settings', 
                                  json=update_data,
                                  headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('settings', data)

    @patch('src.models.user_model.User.find_by_google_id')
    def test_post_notification_settings_invalid_frequency(self, mock_find_user):
        """Test POST /api/notifications/settings with invalid frequency"""
        mock_find_user.return_value = MagicMock(user_id='test_user', email='test@example.com', name='Test User')
        
        update_data = {
            "journal_enabled": True,
            "journal_frequency": "invalid",
            "journal_time": "21:00"
        }
        
        headers = self.get_jwt_headers('test_user')
        headers['Content-Type'] = 'application/json'
        response = self.client.post('/api/notifications/settings', 
                                  json=update_data,
                                  headers=headers)
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    @patch('src.models.user_model.User.find_by_google_id')
    def test_post_notification_settings_invalid_time(self, mock_find_user):
        """Test POST /api/notifications/settings with invalid time format"""
        mock_find_user.return_value = MagicMock(user_id='test_user', email='test@example.com', name='Test User')
        
        update_data = {
            "journal_enabled": True,
            "journal_frequency": "daily",
            "journal_time": "25:00"
        }
        
        headers = self.get_jwt_headers('test_user')
        headers['Content-Type'] = 'application/json'
        response = self.client.post('/api/notifications/settings', 
                                  json=update_data,
                                  headers=headers)
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    @patch('src.services.notification_service.NotificationService.get_journal_prompts')
    def test_get_prompts_success(self, mock_get_prompts):
        """Test GET /api/notifications/prompts"""
        mock_get_prompts.return_value = [
            "Write about the most challenging moment of your day and how you handled it.",
            "Reflect on something that made you smile today, no matter how small."
        ]
        
        headers = self.get_jwt_headers('test_user')
        response = self.client.get('/api/notifications/prompts', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('prompts', data)
        self.assertIsInstance(data['prompts'], list)
        self.assertGreater(len(data['prompts']), 0)

    @patch('src.models.user_model.User.find_by_google_id')
    @patch('src.services.notification_service.NotificationService.send_test_email')
    def test_send_test_email_success(self, mock_send_email, mock_find_user):
        """Test POST /api/notifications/test"""
        mock_find_user.return_value = MagicMock(user_id='test_user', email='test@example.com', name='Test User')
        mock_send_email.return_value = True
        
        headers = self.get_jwt_headers('test_user')
        response = self.client.post('/api/notifications/test', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('message', data)

    def test_send_test_email_unauthorized(self):
        """Test POST /api/notifications/test without authentication"""
        response = self.client.post('/api/notifications/test')
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main() 