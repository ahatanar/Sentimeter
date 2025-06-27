import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import uuid
from src.models.journal_model import JournalEntryModel
from sqlalchemy.orm.exc import NoResultFound

class TestJournalModel(unittest.TestCase):

    @patch('src.models.journal_model.db.session')
    def test_save(self, mock_db_session):
        # Arrange
        journal_entry = JournalEntryModel(
            user_id="test_user",
            entry="Test journal entry",
            sentiment="positive",
            sentiment_score=0.8
        )
        
        # Act
        result = journal_entry.save()
        
        # Assert
        self.assertEqual(result, journal_entry)
        mock_db_session.add.assert_called_once_with(journal_entry)
        mock_db_session.commit.assert_called_once()

    @patch('src.models.journal_model.db.session')
    def test_get_entry(self, mock_db_session):
        # Arrange
        user_id = "test_user"
        timestamp = datetime.now(timezone.utc)
        expected_entry = JournalEntryModel(
            user_id=user_id,
            entry="Test entry",
            timestamp=timestamp
        )
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value.one.return_value = expected_entry
        mock_db_session.query.return_value = mock_query
        
        # Act
        result = JournalEntryModel.get_entry(user_id, timestamp)
        
        # Assert
        self.assertEqual(result, expected_entry)
        mock_db_session.query.assert_called_once_with(JournalEntryModel)

    @patch('src.models.journal_model.db.session')
    def test_get_all_entries(self, mock_db_session):
        # Arrange
        user_id = "test_user"
        entry1 = JournalEntryModel(user_id=user_id, entry="Entry 1")
        entry2 = JournalEntryModel(user_id=user_id, entry="Entry 2")
        expected_entries = [entry1, entry2]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = expected_entries
        mock_db_session.query.return_value = mock_query
        
        # Mock to_dict method
        with patch.object(entry1, 'to_dict', return_value={'entry': 'Entry 1'}):
            with patch.object(entry2, 'to_dict', return_value={'entry': 'Entry 2'}):
                # Act
                result = JournalEntryModel.get_all_entries(user_id, limit=10)
                
                # Assert
                self.assertEqual(len(result), 2)
                mock_db_session.query.assert_called_once_with(JournalEntryModel)

    @patch('src.models.journal_model.db.session')
    def test_delete_entry(self, mock_db_session):
        # Arrange
        entry_id = str(uuid.uuid4())
        mock_entry = JournalEntryModel(entry_id=entry_id, user_id="test_user", entry="Test entry")
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value.one.return_value = mock_entry
        mock_db_session.query.return_value = mock_query
        
        # Act
        result = JournalEntryModel.delete_entry(entry_id)
        
        # Assert
        self.assertTrue(result)
        mock_db_session.query.assert_called_once_with(JournalEntryModel)
        mock_db_session.delete.assert_called_once_with(mock_entry)
        mock_db_session.commit.assert_called_once()

    @patch('src.models.journal_model.db.session')
    def test_delete_entry_not_found(self, mock_db_session):
        # Arrange
        entry_id = str(uuid.uuid4())
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value.one.side_effect = NoResultFound()
        mock_db_session.query.return_value = mock_query
        
        # Act
        result = JournalEntryModel.delete_entry(entry_id)
        
        # Assert
        self.assertFalse(result)
        mock_db_session.query.assert_called_once_with(JournalEntryModel)
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @patch('src.models.journal_model.db.session')
    def test_get_entries_by_keyword(self, mock_db_session):
        # Arrange
        user_id = "test_user"
        keyword = "happy"
        entry1 = JournalEntryModel(user_id=user_id, entry="I am happy today", keywords=["happy", "good"])
        entry2 = JournalEntryModel(user_id=user_id, entry="Feeling happy and content", keywords=["happy", "content"])
        expected_entries = [entry1, entry2]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.all.return_value = expected_entries
        mock_db_session.query.return_value = mock_query
        
        # Mock to_dict method
        with patch.object(entry1, 'to_dict', return_value={'entry': 'I am happy today'}):
            with patch.object(entry2, 'to_dict', return_value={'entry': 'Feeling happy and content'}):
                # Act
                result = JournalEntryModel.get_entries_by_keyword(user_id, keyword)
                
                # Assert
                self.assertEqual(len(result), 2)
                mock_db_session.query.assert_called_once_with(JournalEntryModel)

    @patch('src.models.journal_model.db.session')
    def test_get_top_keywords(self, mock_db_session):
        # Arrange
        user_id = "test_user"
        mock_keywords = [["happy", "good"], ["sad", "bad"], ["happy", "excited"]]
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value.all.return_value = mock_keywords
        mock_db_session.query.return_value = mock_query
        
        # Act
        result = JournalEntryModel.get_all_keywords(user_id)
        
        # Assert
        self.assertEqual(result, mock_keywords)
        mock_db_session.query.assert_called_once_with(JournalEntryModel.keywords)

if __name__ == '__main__':
    unittest.main()  