import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.models.journal_model import JournalEntryModel
from sqlalchemy.orm.exc import NoResultFound

class TestJournalEntryModel(unittest.TestCase):

    @patch('src.models.journal_model.db_session')
    def test_save(self, mock_db_session):
        # Create a test journal entry
        user_id = 'test_user'
        entry = 'This is a test journal entry.'
        sentiment = 'Positive'
        emotions = {'happiness': 0.9}

        journal_entry = JournalEntryModel()
        journal_entry.user_id = user_id
        journal_entry.entry = entry
        journal_entry.sentiment = sentiment
        journal_entry.emotions = emotions

        result = journal_entry.save()

        # Assertions
        mock_db_session.add.assert_called_once_with(journal_entry)
        mock_db_session.commit.assert_called_once()
        self.assertEqual(result, journal_entry)

    @patch('src.models.journal_model.db_session')
    def test_get_entry(self, mock_db_session):
        # Mock the query response
        mock_entry = MagicMock()
        mock_entry.user_id = 'test_user'
        mock_entry.timestamp = datetime(2024, 11, 12, 12, 0, 0, tzinfo=timezone.utc)
        mock_entry.entry = 'Test entry'
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.one.return_value = mock_entry
        mock_db_session.query.return_value = mock_query

        user_id = 'test_user'
        timestamp = datetime(2024, 11, 12, 12, 0, 0, tzinfo=timezone.utc)
        result = JournalEntryModel.get_entry(user_id, timestamp)

        # Assertions
        mock_db_session.query.assert_called_once_with(JournalEntryModel)
        mock_query.filter_by.assert_called_once_with(user_id=user_id, timestamp=timestamp)
        self.assertEqual(result, mock_entry)

    @patch('src.models.journal_model.db_session')
    def test_get_all_entries(self, mock_db_session):
        # Mock the query response
        mock_entry1 = MagicMock()
        mock_entry1.to_dict.return_value = {
            'user_id': 'test_user', 
            'timestamp': '2024-11-12T12:00:00', 
            'entry': 'Entry 1'
        }
        mock_entry2 = MagicMock()
        mock_entry2.to_dict.return_value = {
            'user_id': 'test_user', 
            'timestamp': '2024-11-13T12:00:00', 
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
    def test_delete_entry(self, mock_db_session):
        # Mock the query response
        mock_entry = MagicMock()
        mock_entry.entry_id = 'test_entry_id'
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.one.return_value = mock_entry
        mock_db_session.query.return_value = mock_query

        entry_id = "test_entry_id"
        result = JournalEntryModel.delete_entry(entry_id)

        # Assertions
        mock_db_session.query.assert_called_once_with(JournalEntryModel)
        mock_query.filter_by.assert_called_once_with(entry_id=entry_id)
        mock_db_session.delete.assert_called_once_with(mock_entry)
        mock_db_session.commit.assert_called_once()
        self.assertTrue(result)

    @patch('src.models.journal_model.db_session')
    def test_delete_entry_not_found(self, mock_db_session):
        # Mock NoResultFound exception
        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.one.side_effect = NoResultFound()
        mock_db_session.query.return_value = mock_query

        entry_id = "nonexistent_entry_id"
        result = JournalEntryModel.delete_entry(entry_id)

        # Assertions
        mock_db_session.query.assert_called_once_with(JournalEntryModel)
        mock_query.filter_by.assert_called_once_with(entry_id=entry_id)
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()
        self.assertFalse(result)

    @patch('src.models.journal_model.db_session')
    def test_get_entries_by_keyword(self, mock_db_session):
        # Mock the query response
        mock_entry1 = MagicMock()
        mock_entry1.to_dict.return_value = {
            "user_id": "user123", 
            "keywords": ["work", "stress"], 
            "entry": "Work is stressful."
        }
        mock_entry2 = MagicMock()
        mock_entry2.to_dict.return_value = {
            "user_id": "user123", 
            "keywords": ["work", "rewarding"], 
            "entry": "Work is rewarding."
        }
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_entry1, mock_entry2]
        mock_db_session.query.return_value = mock_query

        keyword = "work"
        user_id = "user123"
        entries = JournalEntryModel.get_entries_by_keyword(user_id, keyword)

        # Assertions
        mock_db_session.query.assert_called_once_with(JournalEntryModel)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["keywords"], ["work", "stress"])
        self.assertEqual(entries[1]["keywords"], ["work", "rewarding"])
    
    @patch('src.models.journal_model.db_session')
    def test_get_top_keywords(self, mock_db_session):
        # Mock the query response
        mock_result1 = MagicMock()
        mock_result1.keywords = ["work", "stress", "growth"]
        mock_result2 = MagicMock()
        mock_result2.keywords = ["work", "rewarding", "happiness"]
        mock_result3 = MagicMock()
        mock_result3.keywords = ["stress", "growth", "productivity"]
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.all.return_value = [mock_result1, mock_result2, mock_result3]
        mock_db_session.query.return_value = mock_query

        user_id = "user123"
        top_keywords = JournalEntryModel.get_top_keywords(user_id, top_n=3)

        # Assertions
        mock_db_session.query.assert_called_once_with(JournalEntryModel.keywords)
        mock_query.filter_by.assert_called_once_with(user_id=user_id)
        self.assertEqual(len(top_keywords), 3)
        # Check that work appears twice, stress appears twice, etc.
        keywords_dict = dict(top_keywords)
        self.assertEqual(keywords_dict.get("work"), 2)
        self.assertEqual(keywords_dict.get("stress"), 2)  