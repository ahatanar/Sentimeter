import uuid
from datetime import datetime
from src.database import get_table

class JournalEntryModel:
    TABLE_NAME = "journals"

    def __init__(self, user_id, entry, sentiment=None, emotions=None, timestamp=None):
        self.user_id = user_id
        self.timestamp = timestamp or datetime.now().isoformat()
        self.entry_id = str(uuid.uuid4())
        self.entry = entry
        self.sentiment = sentiment
        self.emotions = emotions

    def save(self):
        """Save the journal entry to DynamoDB."""
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

    @classmethod
    def get_entry(cls, user_id, timestamp):
        """Retrieve a specific journal entry by user ID and timestamp."""
        journals_table = get_table(cls.TABLE_NAME)
        response = journals_table.get_item(Key={"user_id": user_id, "timestamp": timestamp})
        return response.get("Item")

    @classmethod
    def get_all_entries(cls, user_id):
        """Retrieve all journal entries for a user."""
        journals_table = get_table(cls.TABLE_NAME)
        response = journals_table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key("user_id").eq(user_id))
        return response.get("Items", [])

    @classmethod
    def delete_entry(cls, user_id, timestamp):
        """Delete a journal entry by user ID and timestamp."""
        journals_table = get_table(cls.TABLE_NAME)
        journals_table.delete_item(Key={"user_id": user_id, "timestamp": timestamp})
