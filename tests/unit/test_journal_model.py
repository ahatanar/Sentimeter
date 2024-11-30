import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.models.journal_model import JournalEntryModel
from boto3.dynamodb.conditions import Key, Attr

class TestJournalEntryModel(unittest.TestCase):

    @patch('src.models.journal_model.get_table')
    def test_save(self, mock_get_table):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        user_id = 'test_user'
        entry = 'This is a test journal entry.'
        sentiment = 'Positive'
        emotions = {'happiness': 0.9}

        journal_entry = JournalEntryModel(user_id, entry, sentiment, emotions)

        result = journal_entry.save()

        # Assertions
        mock_table.put_item.assert_called_once()
        called_args = mock_table.put_item.call_args[1]['Item']
        self.assertEqual(called_args['user_id'], user_id)
        self.assertEqual(called_args['entry'], entry)
        self.assertEqual(called_args['sentiment'], sentiment)
        self.assertEqual(called_args['emotions'], emotions)
        self.assertEqual(result, journal_entry)

    @patch('src.models.journal_model.get_table')
    def test_get_entry(self, mock_get_table):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        expected_item = {
            'user_id': 'test_user',
            'timestamp': '2024-11-12T12:00:00',
            'entry_id': 'some-uuid',
            'entry': 'Test entry',
            'sentiment': 'Positive',
            'emotions': {'happiness': 0.9},
        }
        mock_table.get_item.return_value = {'Item': expected_item}

        user_id = 'test_user'
        timestamp = '2024-11-12T12:00:00'
        entry = JournalEntryModel.get_entry(user_id, timestamp)

        # Assertions
        mock_table.get_item.assert_called_once_with(Key={'user_id': user_id, 'timestamp': timestamp})
        self.assertEqual(entry, expected_item)

    @patch('src.models.journal_model.get_table')
    def test_get_all_entries(self, mock_get_table):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        expected_items = [
            {'user_id': 'test_user', 'timestamp': '2024-11-12T12:00:00', 'entry_id': 'uuid1', 'entry': 'Entry 1'},
            {'user_id': 'test_user', 'timestamp': '2024-11-13T12:00:00', 'entry_id': 'uuid2', 'entry': 'Entry 2'},
        ]
        mock_table.query.return_value = {'Items': expected_items}

        user_id = 'test_user'
        entries = JournalEntryModel.get_all_entries(user_id)

        # Assertions
        mock_table.query.assert_called_once()
        self.assertEqual(entries, expected_items)

   

    @patch('src.models.journal_model.get_table')
    def test_delete_entry(self, mock_get_table):
        # Mock the DynamoDB table
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        # Mock the query response
        mock_table.query.return_value = {
            "Items": [{"user_id": "test_user", "timestamp": "2024-11-12T12:00:00"}]
        }

        # Input values
        entry_id = "test_entry_id"

        # Call the method under test
        result = JournalEntryModel.delete_entry(entry_id)

        # Assertions
        mock_table.query.assert_called_once_with(
            IndexName="entry_id-index",
            KeyConditionExpression=Key("entry_id").eq(entry_id),
        )
        mock_table.delete_item.assert_called_once_with(
            Key={"user_id": "test_user", "timestamp": "2024-11-12T12:00:00"}
        )
        self.assertTrue(result)

    @patch('src.models.journal_model.get_table')
    def test_delete_entry_not_found(self, mock_get_table):
        # Mock the DynamoDB table
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        # Mock the query response to return no items
        mock_table.query.return_value = {"Items": []}

        # Input values
        entry_id = "nonexistent_entry_id"

        # Call the method under test
        result = JournalEntryModel.delete_entry(entry_id)

        # Assertions
        mock_table.query.assert_called_once_with(
            IndexName="entry_id-index",
            KeyConditionExpression=Key("entry_id").eq(entry_id),
        )
        mock_table.delete_item.assert_not_called()
        self.assertFalse(result)




    @patch('src.models.journal_model.get_table')
    def test_get_entries_by_keyword(self, mock_get_table):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        mock_response = {
            "Items": [
                {"user_id": "user123", "keywords": ["work", "stress"], "entry": "Work is stressful."},
                {"user_id": "user123", "keywords": ["work", "rewarding"], "entry": "Work is rewarding."},
            ]
        }
        mock_table.scan.return_value = mock_response

        keyword = "work"
        user_id = "user123"
        entries = JournalEntryModel.get_entries_by_keyword(user_id, keyword)

        # Assertions
        mock_get_table.assert_called_once_with(JournalEntryModel.TABLE_NAME)
        mock_table.scan.assert_called_once()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["keywords"], ["work", "stress"])
        self.assertEqual(entries[1]["keywords"], ["work", "rewarding"])
    
    @patch('src.models.journal_model.get_table')
    def test_get_top_keywords(self, mock_get_table):
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table

        mock_response = {
            "Items": [
                {"keywords": ["work", "stress", "growth"]},
                {"keywords": ["work", "rewarding", "happiness"]},
                {"keywords": ["stress", "growth", "productivity"]},
            ]
        }
        mock_table.query.return_value = mock_response

        user_id = "user123"
        top_keywords = JournalEntryModel.get_top_keywords(user_id, top_n=3)

        # Assertions
        mock_get_table.assert_called_once_with(JournalEntryModel.TABLE_NAME)
        mock_table.query.assert_called_once()
        self.assertEqual(len(top_keywords), 3)
        self.assertEqual(top_keywords[0], ("work", 2))  
        self.assertEqual(top_keywords[1], ("stress", 2))  
        self.assertEqual(top_keywords[2], ("growth", 2))  