import unittest
from unittest.mock import patch, MagicMock
from src.models.journal_model import JournalEntryModel
from src.services.journal_service import JournalService

class TestJournalService(unittest.TestCase):

    @patch('src.models.journal_model.db_session')
    def test_get_all_entries_success(self, mock_db_session):
        # Mock the query response
        mock_entry1 = MagicMock()
        mock_entry1.to_dict.return_value = {
            'user_id': 'test_user', 
            'timestamp': '2024-11-12T12:00:00', 
            'entry_id': 'uuid1', 
            'entry': 'Entry 1'
        }
        mock_entry2 = MagicMock()
        mock_entry2.to_dict.return_value = {
            'user_id': 'test_user', 
            'timestamp': '2024-11-13T12:00:00', 
            'entry_id': 'uuid2', 
            'entry': 'Entry 2'
        }
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_entry1, mock_entry2]
        mock_db_session.query.return_value = mock_query

        user_id = 'test_user'
        entries = JournalEntryModel.get_all_entries(user_id)

        # Assertions
        mock_db_session.query.assert_called_once_with(JournalEntryModel)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]['entry'], 'Entry 1')
        self.assertEqual(entries[1]['entry'], 'Entry 2')

    @patch('src.models.journal_model.db_session')
    def test_get_all_entries_dynamodb_error(self, mock_db_session):
        # Mock database error
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.side_effect = Exception("Database error")
        mock_db_session.query.return_value = mock_query

        with self.assertRaises(Exception) as context:
            JournalEntryModel.get_all_entries("test_user")

        # Assertions
        self.assertEqual(str(context.exception), "Database error")
        mock_db_session.query.assert_called_once_with(JournalEntryModel)

    @patch('src.models.journal_model.db_session')
    def test_get_all_entries_empty(self, mock_db_session):
        # Mock empty response
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db_session.query.return_value = mock_query

        entries = JournalEntryModel.get_all_entries("test_user")

        # Assertions
        self.assertEqual(entries, [])
        mock_db_session.query.assert_called_once_with(JournalEntryModel)

    @patch('src.models.journal_model.JournalEntryModel.get_entries_by_month')
    def test_get_entries_by_month(self, mock_get_entries_by_month):
        mock_get_entries_by_month.return_value = [
            {"entry_id": "uuid1", "entry": "Test entry 1", "timestamp": "2024-11-01T08:30:00"},
            {"entry_id": "uuid2", "entry": "Test entry 2", "timestamp": "2024-11-02T14:45:00"}
        ]

        user_id = "test_user"
        year = "2024"
        month = "11"
        entries = JournalService.get_entries_by_month(user_id, year, month)

        # Assertions
        mock_get_entries_by_month.assert_called_once_with(user_id, year, month)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["entry_id"], "uuid1")