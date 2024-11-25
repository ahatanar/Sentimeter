from datetime import datetime
from src.models.journal_model import JournalEntryModel
from src.services.sentiment_analysis import analyze_sentiment


class JournalService:
    @staticmethod
    def create_journal_entry(user_id, entry):
        """
        Create and save a new journal entry.
        :param user_id: ID of the user creating the entry.
        :param entry: Text of the journal entry.
        :return: Entry ID of the created journal entry.
        """
        # Analyze sentiment
        sentiment, confidence = analyze_sentiment(entry)

        # Create and save the journal entry
        journal_entry = JournalEntryModel(
            user_id=user_id,
            entry=entry,
            sentiment=sentiment,
            emotions=None,  # Placeholder for future emotion data
            timestamp=datetime.now().isoformat()
        )
        journal_entry.save()

        return journal_entry.entry_id

    @staticmethod
    def get_all_journal_entries(user_id):
        """
        Retrieve all journal entries for a specific user.
        :param user_id: ID of the user.
        :return: List of journal entries.
        """
        return JournalEntryModel.get_all_entries(user_id)

    @staticmethod
    def get_journal_entry(user_id, entry_id):
        """
        Retrieve a specific journal entry by entry ID.
        :param user_id: ID of the user.
        :param entry_id: Entry ID of the journal entry.
        :return: Journal entry object or None if not found.
        """
        return JournalEntryModel.get_entry_by_id(user_id, entry_id)

    @staticmethod
    def delete_journal_entry(entry_id):
        """
        Delete a specific journal entry by entry ID.
        :param entry_id: Entry ID of the journal entry to delete.
        :return: True if deletion was successful, False otherwise.
        """
        return JournalEntryModel.delete_by_entry_id(entry_id)