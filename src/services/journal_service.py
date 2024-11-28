from datetime import datetime
from src.models.journal_model import JournalEntryModel
from src.services.text_service import TextAnalysisService
from src.services.weather_service import WeatherService

class JournalService:
    @staticmethod
    def create_journal_entry(user_id, entry,ip_address):
        """
        Create and save a new journal entry.
        :param user_id: ID of the user creating the entry.
        :param entry: Text of the journal entry.
        :return: Dictionary with saved entry details.
        """
        print("Error in location")

        location = WeatherService.get_location_from_ip(ip_address)
        print("Error in weather")

        weather_data = WeatherService.get_weather_by_location(location)
        print("Error in description")

        weather_description = TextAnalysisService.generate_weather_description(weather_data)
        print("Error in sentiment")

        sentiment, sentiment_score = TextAnalysisService.analyze_sentiment(entry)
        print("Error in keywords")

        key_words  = TextAnalysisService.extract_keywords(entry)
        print("pre creation of entry service")
        print(key_words)
        journal_entry = JournalEntryModel(
            user_id=user_id,
            entry=entry,
            sentiment=sentiment,
            emotions=None, 
            timestamp=datetime.now().isoformat(),
            keywords = key_words,
            location=location,
            weather=weather_description,
            sentiment_score=sentiment_score

        )
        saved_entry = journal_entry.save()  

        return {
            "entry_id": saved_entry.entry_id,
            "user_id": saved_entry.user_id,
            "timestamp": saved_entry.timestamp,
            "sentiment": saved_entry.sentiment,
            "entry": saved_entry.entry,
            "keywords":key_words
        }
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

    @staticmethod
    def get_recent_entries(user_id):
        """
        Fetch the last 10 journal entries for a user.
        :param user_id: The user's ID.
        :return: A list of the 10 most recent journal entries.
        """
        return JournalEntryModel.get_recent_entries(user_id)

    @staticmethod
    def get_entries_by_month(user_id, year, month):
        """
        Fetch journal entries for a specific month and year.
        :param user_id: The user's ID.
        :param year: Year to filter by.
        :param month: Month to filter by.
        :return: A list of journal entries for the specified month and year.
        """
        return JournalEntryModel.get_entries_by_month(user_id, year, month)

    @staticmethod
    def get_dashboard_data(user_id):
        """
        Generate heatmap data (entry counts by day) for the dashboard.
        :param user_id: The user's ID.
        :return: A dictionary with date counts.
        """
        return JournalEntryModel.get_dashboard_data(user_id)
    
    @staticmethod
    def get_entries_by_month(user_id, year, month):
        """
        Fetch journal entries for a specific month and year.
        :param user_id: The user's ID.
        :param year: Year to filter by (e.g., 2024).
        :param month: Month to filter by (e.g., 11 for November).
        :return: A list of journal entries for the specified month and year.
        """
        return JournalEntryModel.get_entries_by_month(user_id, year, month)
    @staticmethod
    def get_heatmap_data(user_id):
        """
        Fetch heatmap data for the last 365 days.
        :param user_id: The user's ID.
        :return: A dictionary with dates as keys and entry counts as values.
        """
        return JournalEntryModel.get_heatmap_data(user_id)
    
    @staticmethod
    def get_dashboard_sentiments(user_id):
        return {
            "last_week": JournalEntryModel.get_last_week_sentiments(user_id),
            "last_month": JournalEntryModel.get_last_month_sentiments(user_id),
            "last_year": JournalEntryModel.get_last_year_sentiments(user_id)
        }


    @staticmethod
    def get_entries_by_keyword(user_id, keyword):
        """
        Retrieve all journal entries for a user that contain a specific keyword.
        """
        return JournalEntryModel.get_entries_by_keyword(user_id, keyword)

    @staticmethod
    def get_top_keywords(user_id, top_n=10):
        """
        Retrieve the top N most common keywords across all entries for a user.
        """
        return JournalEntryModel.get_top_keywords(user_id, top_n)