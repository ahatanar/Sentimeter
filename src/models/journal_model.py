import uuid
from datetime import datetime
from src.database import get_table
import boto3
from boto3.dynamodb.conditions import Key

class JournalEntryModel:
    TABLE_NAME = "journals"

    def __init__(self, user_id, entry, sentiment=None, emotions=None, timestamp=None):
        """
        Initialize a new journal entry model.
        :param user_id: ID of the user creating the entry.
        :param entry: The journal entry text.
        :param sentiment: The sentiment of the entry (optional).
        :param emotions: The emotions data of the entry (optional).
        :param timestamp: The timestamp of the entry (optional, defaults to now).
        """
        self.user_id = user_id
        self.timestamp = timestamp or datetime.now().isoformat()
        self.entry_id = str(uuid.uuid4())
        self.entry = entry
        self.sentiment = sentiment
        self.emotions = emotions
        print(f"[DEBUG] Initialized JournalEntryModel: {self.__dict__}")

    def save(self):
        """
        Save the journal entry to DynamoDB and return the entry instance.
        :return: The current instance of JournalEntryModel.
        """
        try:
            journals_table = get_table(self.TABLE_NAME)
            journals_table.put_item(
                Item={
                    "user_id": self.user_id,
                    "timestamp": self.timestamp,
                    "entry_id": self.entry_id,
                    "entry": self.entry,
                    "sentiment": self.sentiment,
                    "emotions": self.emotions,
                }
            )
            print(f"[DEBUG] Successfully saved journal entry: {self.entry_id}")
            return self
        except Exception as e:
            print(f"[ERROR] Failed to save journal entry: {e}")
            raise

    @classmethod
    def get_entry(cls, user_id, timestamp):
        """
        Retrieve a specific journal entry by user ID and timestamp.
        :param user_id: The user's ID.
        :param timestamp: The timestamp of the desired entry.
        :return: The journal entry as a dictionary or None if not found.
        """
        try:
            journals_table = get_table(cls.TABLE_NAME)
            response = journals_table.get_item(Key={"user_id": user_id, "timestamp": timestamp})
            entry = response.get("Item")
            print(f"[DEBUG] Retrieved journal entry: {entry}")
            return entry
        except Exception as e:
            print(f"[ERROR] Failed to retrieve journal entry: {e}")
            raise

    @classmethod
    def get_all_entries(cls, user_id):
        """
        Retrieve all journal entries for a user.
        :param user_id: The user's ID.
        :return: A list of journal entries.
        """
        try:
            journals_table = get_table(cls.TABLE_NAME)
            response = journals_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id)

            )
            entries = response.get("Items", [])
            print(f"[DEBUG] Retrieved all journal entries for user {user_id}: {entries}")
            return entries
        except Exception as e:
            print(f"[ERROR] Failed to retrieve all journal entries: {e}")
            raise

    @classmethod
    def delete_entry(cls, user_id, timestamp):
        """
        Delete a journal entry by user ID and timestamp.
        :param user_id: The user's ID.
        :param timestamp: The timestamp of the entry to delete.
        :return: None
        """
        try:
            journals_table = get_table(cls.TABLE_NAME)
            journals_table.delete_item(Key={"user_id": user_id, "timestamp": timestamp})
            print(f"[DEBUG] Deleted journal entry for user {user_id} at {timestamp}")
        except Exception as e:
            print(f"[ERROR] Failed to delete journal entry: {e}")
            raise
