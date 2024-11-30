import unittest
from unittest.mock import patch, MagicMock
from src.models.journal_model import JournalEntryModel
from src.services.journal_service import JournalService

class TestJournalEntryModel(unittest.TestCase):

    @patch('src.models.journal_model.get_table')  
    @patch('src.models.journal_model.Key')  
    def test_get_all_entries_success(self, mock_key, mock_get_table):
        mock_eq = MagicMock()
        mock_key.return_value.eq.return_value = mock_eq

        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        expected_items = [
            {'user_id': 'test_user', 'timestamp': '2024-11-12T12:00:00', 'entry_id': 'uuid1', 'entry': 'Entry 1'},
            {'user_id': 'test_user', 'timestamp': '2024-11-13T12:00:00', 'entry_id': 'uuid2', 'entry': 'Entry 2'},
        ]
        mock_table.query.return_value = {'Items': expected_items}

        user_id = 'test_user'
        entries = JournalEntryModel.get_all_entries(user_id)

        mock_get_table.assert_called_once_with(JournalEntryModel.TABLE_NAME)
        mock_key.assert_called_once_with("user_id")
        mock_key.return_value.eq.assert_called_once_with(user_id)
        mock_table.query.assert_called_once_with(KeyConditionExpression=mock_eq)
        self.assertEqual(entries, expected_items)

    @patch('src.models.journal_model.get_table')  
    @patch('src.models.journal_model.Key')  
    def test_get_all_entries_dynamodb_error(self, mock_key, mock_get_table):
        mock_eq = MagicMock()
        mock_key.return_value.eq.return_value = mock_eq

        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        mock_table.query.side_effect = Exception("DynamoDB error")

        with self.assertRaises(Exception) as context:
            JournalEntryModel.get_all_entries("test_user")

        # Assertions
        self.assertEqual(str(context.exception), "DynamoDB error")
        mock_get_table.assert_called_once_with(JournalEntryModel.TABLE_NAME)
        mock_key.assert_called_once_with("user_id")
        mock_key.return_value.eq.assert_called_once_with("test_user")
        mock_table.query.assert_called_once_with(KeyConditionExpression=mock_eq)

    @patch('src.models.journal_model.get_table')  
    @patch('src.models.journal_model.Key') 
    def test_get_all_entries_empty(self, mock_key, mock_get_table):
        mock_eq = MagicMock()
        mock_key.return_value.eq.return_value = mock_eq

        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        mock_table.query.return_value = {'Items': []}

        entries = JournalEntryModel.get_all_entries("test_user")

        # Assertions
        self.assertEqual(entries, [])
        mock_get_table.assert_called_once_with(JournalEntryModel.TABLE_NAME)
        mock_key.assert_called_once_with("user_id")
        mock_key.return_value.eq.assert_called_once_with("test_user")
        mock_table.query.assert_called_once_with(KeyConditionExpression=mock_eq)

    @patch('src.models.journal_model.get_table')
    @patch('src.services.journal_service.JournalEntryModel.get_entries_by_month')
    def test_get_entries_by_month(self, mock_get_entries_by_month, mock_get_table):
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