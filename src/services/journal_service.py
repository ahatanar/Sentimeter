from datetime import datetime
from src.models.journal_model import JournalEntryModel
from src.services.text_service import TextAnalysisService
from src.services.weather_service import WeatherService

class JournalService:
    @staticmethod
    def create_journal_entry(user_id, entry, ip_address, optional_date=None, location_data=None):
        """
        Create and save a new journal entry.
        :param user_id: ID of the user creating the entry.
        :param entry: Text of the journal entry.
        :param ip_address: IP address for location/weather lookup.
        :param optional_date: Optional timestamp for the journal entry (ISO format string).
        :param location_data: Optional geolocation data (latitude and longitude).
        :return: Dictionary with saved entry details.
        """
        if location_data:
            location = WeatherService.reverse_geocode(location_data['latitude'],location_data['longitude'])
        else:
            location = WeatherService.get_location_from_ip(ip_address) 
        print(location)
        weather_data = WeatherService.get_weather_by_location(location)
        weather_description = TextAnalysisService.generate_weather_description(weather_data)


        sentiment, sentiment_score = TextAnalysisService.analyze_sentiment(entry)
        key_words = TextAnalysisService.extract_keywords(entry)

        timestamp = (
            datetime.fromisoformat(optional_date) if optional_date else datetime.now()
        )

        journal_entry = JournalEntryModel(
            user_id=user_id,
            entry=entry,
            sentiment=sentiment,
            emotions=None,
            timestamp=timestamp.isoformat(),
            keywords=key_words,
            location=location,
            weather=weather_description,
            sentiment_score=sentiment_score,
        )

        print("before save")
        saved_entry = journal_entry.save()

        return saved_entry.to_dict()

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
        return JournalEntryModel.delete_entry(entry_id)

    @staticmethod
    def get_recent_entries(user_id):
        """
        Fetch the last 12 journal entries for a user.
        :param user_id: The user's ID.
        :return: A list of the 12 most recent journal entries.
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