import unittest
from unittest.mock import patch
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from src.controllers.jorunal_controller import journal_bp


class TestJournalRoutes(unittest.TestCase):

    def setUp(self):
        """
        Set up the Flask test client and push an application context.
        """
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        self.app.register_blueprint(journal_bp)
        self.jwt = JWTManager(self.app)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """
        Clean up the application context after each test.
        """
        self.app_context.pop()

    def get_jwt_headers(self, user_id):
        """
        Helper method to generate JWT headers for tests.
        """
        access_token = create_access_token(identity={"google_id": user_id})
        return {'Authorization': f'Bearer {access_token}'}

    @patch('src.services.journal_service.JournalService.create_journal_entry')
    def test_create_journal_entry_success(self, mock_create_journal_entry):
        mock_create_journal_entry.return_value = 'test-entry-id'

        headers = self.get_jwt_headers('test_user')
        response = self.client.post(
            '/api/journals', json={'entry': 'Test entry content'}, headers=headers
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['message'], 'Journal entry created successfully')
        self.assertEqual(response.json['entry_id'], 'test-entry-id')
        mock_create_journal_entry.assert_called_once_with(
            'test_user', 'Test entry content', unittest.mock.ANY
        )

    @patch('src.services.journal_service.JournalService.get_all_journal_entries')
    def test_get_all_journal_entries_success(self, mock_get_all_journal_entries):
        mock_get_all_journal_entries.return_value = [{'id': '1', 'entry': 'Entry 1'}]

        headers = self.get_jwt_headers('test_user')
        response = self.client.get('/api/journals', headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Journal entries retrieved')
        self.assertEqual(response.json['entries'], [{'id': '1', 'entry': 'Entry 1'}])
        mock_get_all_journal_entries.assert_called_once_with('test_user')

    @patch('src.services.journal_service.JournalService.get_all_journal_entries')
    def test_get_all_journal_entries_not_found(self, mock_get_all_journal_entries):
        mock_get_all_journal_entries.return_value = []

        headers = self.get_jwt_headers('test_user')
        response = self.client.get('/api/journals', headers=headers)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['message'], 'No journal entries found')
        mock_get_all_journal_entries.assert_called_once_with('test_user')

    @patch('src.services.journal_service.JournalService.delete_journal_entry')
    def test_delete_journal_entry_success(self, mock_delete_journal_entry):
        mock_delete_journal_entry.return_value = True

        headers = self.get_jwt_headers('test_user')
        response = self.client.delete('/api/journals/test-entry-id', headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Journal entry deleted successfully')
        mock_delete_journal_entry.assert_called_once_with('test-entry-id')

    @patch('src.services.journal_service.JournalService.delete_journal_entry')
    def test_delete_journal_entry_not_found(self, mock_delete_journal_entry):
        mock_delete_journal_entry.return_value = False

        headers = self.get_jwt_headers('test_user')
        response = self.client.delete('/api/journals/test-entry-id', headers=headers)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Journal entry not found')
        mock_delete_journal_entry.assert_called_once_with('test-entry-id')

    @patch('src.services.journal_service.JournalService.get_heatmap_data')
    def test_get_heatmap_data_success(self, mock_get_heatmap_data):
        mock_get_heatmap_data.return_value = {
            "2024-11-25": 3,
            "2024-11-24": 1,
            "2024-11-23": 0,
            "2024-11-22": 2,
        }

        headers = self.get_jwt_headers('test_user')
        response = self.client.get('/api/journals/heatmap', headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["2024-11-25"], 3)
        mock_get_heatmap_data.assert_called_once_with('test_user')

    @patch('src.services.journal_service.JournalService.create_journal_entry')
    def test_create_journal_entry_internal_error(self, mock_create_journal_entry):
        mock_create_journal_entry.side_effect = Exception('Something went wrong')

        headers = self.get_jwt_headers('test_user')
        response = self.client.post(
            '/api/journals', json={'entry': 'Test entry content'}, headers=headers
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json['error'], 'Something went wrong')

