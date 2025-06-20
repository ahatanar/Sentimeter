import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, url_for
from src.controllers.auth_controller import auth_bp
from flask_jwt_extended import JWTManager


class TestAuthController(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        self.app.register_blueprint(auth_bp)
        self.jwt = JWTManager(self.app)
        self.client = self.app.test_client()

        # Mock environment variables for Google OAuth
        self.env_patcher = patch.dict('os.environ', {
            "GOOGLE_CLIENT_ID": "test-client-id",
            "GOOGLE_CLIENT_SECRET": "test-client-secret"
        })
        self.env_patcher.start()

        # Push the application context
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.env_patcher.stop()
        self.app_context.pop()
        patch.stopall()

    @patch('src.controllers.auth_controller.requests.get')
    def test_login_success(self, mock_requests_get):
        # Mock Google discovery document
        mock_requests_get.return_value.json.return_value = {
            "authorization_endpoint": "https://test-auth-endpoint"
        }

        # Call the login endpoint
        response = self.client.get('/api/auth/login')

        # Assertions
        self.assertEqual(response.status_code, 302)
        self.assertIn("https://test-auth-endpoint", response.location)

    @patch('src.controllers.auth_controller.requests.get')
    def test_login_failure(self, mock_requests_get):
        # Mock Google discovery document to raise an exception
        mock_requests_get.side_effect = Exception("Discovery document error")

        # Call the login endpoint
        response = self.client.get('/api/auth/login')

        # Assertions
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], 'Failed to initiate login')
    @patch('src.controllers.auth_controller.requests.get')
    @patch('src.controllers.auth_controller.requests.post')
    @patch('src.controllers.auth_controller.client')
    @patch('src.controllers.auth_controller.User')
    def test_callback_success(
        self, mock_user_model, mock_client, mock_requests_post, mock_requests_get
    ):
        # Mock Google discovery document
        mock_requests_get.return_value.json.side_effect = [
            {"token_endpoint": "https://test-token-endpoint", "userinfo_endpoint": "https://test-userinfo-endpoint"},
            {"sub": "test-google-id", "email": "test@example.com", "name": "Test User"},
        ]

        # Mock token request preparation
        mock_client.prepare_token_request.return_value = (
            "https://test-token-endpoint",
            {"Content-Type": "application/x-www-form-urlencoded"},
            "code=test-code&client_id=test-client-id"
        )

        # Mock token exchange
        mock_requests_post.return_value.status_code = 200
        mock_requests_post.return_value.text = '{"access_token": "test-access-token"}'

        # Mock token parsing
        mock_client.parse_request_body_response.return_value = None

        # Mock user info retrieval
        mock_client.add_token.return_value = (
            "https://test-userinfo-endpoint",
            {"Authorization": "Bearer test-access-token"},
            None,
        )
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {
            "sub": "test-google-id",
            "email": "test@example.com",
            "name": "Test User",
        }

        # Mock user model methods
        mock_user_model.find_by_google_id.return_value = None
        mock_user_model.save.return_value = None

        # Call the callback endpoint with a valid query string
        response = self.client.get('/api/auth/callback?code=test-code')

        self.assertEqual(response.status_code, 303)  # Ensure the redirect occurs

        # Assertions for cookie
        cookies = response.headers.getlist('Set-Cookie')
        self.assertTrue(any("access_token_cookie=" in cookie for cookie in cookies))  # Ensure cookie is set

        mock_user_model.find_by_google_id.assert_called_once_with("test-google-id")
        mock_user_model.save.assert_called_once_with("test-google-id", "test@example.com", "Test User")

    @patch('src.controllers.auth_controller.requests.get')
    def test_callback_failure(self, mock_requests_get):
        # Mock Google discovery document to raise an exception
        mock_requests_get.side_effect = Exception("Callback error")

        # Call the callback endpoint
        response = self.client.get('/api/auth/callback?code=test-code')

        # Assertions
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], 'Failed to process callback')

    def test_callback_missing_code(self):
        response = self.client.get('/api/auth/callback')

    
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Missing code parameter')


if __name__ == '__main__':
    unittest.main()
