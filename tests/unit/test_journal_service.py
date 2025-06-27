import unittest
from unittest.mock import patch, MagicMock
from src.models.journal_model import JournalEntryModel
from src.services.journal_service import JournalService

class TestJournalService(unittest.TestCase):

    @patch('src.models.journal_model.db.session')
    def test_get_all_entries_success(self, mock_db_session):
        # Arrange
        user_id = "test_user"
        mock_entry1 = MagicMock()
        mock_entry1.to_dict.return_value = {
            "entry_id": "entry1",
            "user_id": user_id,
            "entry": "Test entry 1",
            "sentiment": "positive"
        }
        mock_entry2 = MagicMock()
        mock_entry2.to_dict.return_value = {
            "entry_id": "entry2", 
            "user_id": user_id,
            "entry": "Test entry 2",
            "sentiment": "negative"
        }
        
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_entry1, mock_entry2]
        mock_db_session.query.return_value = mock_query
        
        # Act
        result = JournalEntryModel.get_all_entries(user_id)
        
        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["entry"], "Test entry 1")
        self.assertEqual(result[1]["entry"], "Test entry 2")
        mock_db_session.query.assert_called_once_with(JournalEntryModel)

    @patch('src.models.journal_model.db.session')
    def test_get_all_entries_dynamodb_error(self, mock_db_session):
        # Arrange
        user_id = "test_user"
        mock_db_session.query.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with self.assertRaises(Exception):
            JournalEntryModel.get_all_entries(user_id)
        
        mock_db_session.query.assert_called_once_with(JournalEntryModel)

    @patch('src.models.journal_model.db.session')
    def test_get_all_entries_empty(self, mock_db_session):
        # Arrange
        user_id = "test_user"
        
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        # Act
        result = JournalEntryModel.get_all_entries(user_id)
        
        # Assert
        self.assertEqual(result, [])
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

if __name__ == '__main__':
    unittest.main()