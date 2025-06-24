from datetime import datetime, timezone
from src.models.journal_model import JournalEntryModel
from dateutil.parser import parse
from src.services.text_service import TextAnalysisService
from src.services.weather_service import WeatherService
from collections import Counter
from datetime import timedelta

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
        weather_data = WeatherService.get_weather_by_location(location)
        weather_description = TextAnalysisService.generate_weather_description(weather_data)


        sentiment, sentiment_score = TextAnalysisService.analyze_sentiment(entry)
        key_words = TextAnalysisService.extract_keywords(entry)
        timestamp = parse(optional_date) if optional_date else datetime.now()
        embedding_vector = TextAnalysisService.generate_openai_embedding(entry)

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
            embedding=embedding_vector,
        )

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
    def get_heatmap_data(user_id, days=365):
        """
        Fetch heatmap data for the last 365 days.
        :param user_id: The user's ID.
        :return: A dictionary with dates as keys and entry counts as values.
        """
        today = datetime.now(timezone.utc)
        start_date = today - timedelta(days=days)
        try:
            timestamps = JournalEntryModel.get_entry_timestamps_in_range(user_id, start_date, today)
            date_counts = Counter(ts.date().isoformat() for ts in timestamps)
            heatmap_data = {
                (today - timedelta(days=i)).strftime('%Y-%m-%d'): date_counts.get(
                    (today - timedelta(days=i)).strftime('%Y-%m-%d'), 0)
                for i in range(days)
            }
            return heatmap_data
        except Exception as e:
            print(f"[ERROR] Failed to generate heatmap data: {e}")
            return {}
    
    @staticmethod
    def get_dashboard_sentiments(user_id):
    return {
        "last_week": JournalService.get_last_week_sentiments(user_id),
        "last_month": JournalService.get_last_month_sentiments(user_id),
        "last_year": JournalService.get_last_year_sentiments(user_id)
    }

    @staticmethod
    def get_last_week_sentiments(user_id):
        today = datetime.now(timezone.utc)
        start = today - timedelta(days=6)
        raw = JournalEntryModel.get_sentiments_by_date(user_id, start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
        from collections import defaultdict
        grouped = defaultdict(list)
        for e in raw:
            grouped[e["timestamp"].date().isoformat()].append(e["sentiment_score"])
        return [
            {
                "day": (start + timedelta(days=i)).strftime('%A'),
                "average_sentiment": sum(grouped.get((start + timedelta(days=i)).strftime('%Y-%m-%d'), [])) /
                                     max(len(grouped.get((start + timedelta(days=i)).strftime('%Y-%m-%d'), [])), 1)
            }
            for i in range(7)
        ]

    @staticmethod
    def get_last_month_sentiments(user_id):
        today = datetime.now(timezone.utc)
        start = today - timedelta(days=29)
        raw = JournalEntryModel.get_sentiments_by_date(user_id, start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
        from collections import defaultdict
        grouped = defaultdict(list)
        for e in raw:
            days_ago = (today - e["timestamp"]).days
            if days_ago <= 6:
                label = "This week"
            elif days_ago <= 13:
                label = "Last week"
            elif days_ago <= 20:
                label = "2 weeks ago"
            elif days_ago <= 27:
                label = "3 weeks ago"
            else:
                label = "4 weeks ago"
            grouped[label].append(e["sentiment_score"])
        labels = ["4 weeks ago", "3 weeks ago", "2 weeks ago", "Last week", "This week"]
        return [
            {
                "week_label": label,
                "average_sentiment": sum(grouped[label]) / len(grouped[label]) if grouped[label] else 0
            }
            for label in labels
        ]

    @staticmethod
    def get_last_year_sentiments(user_id):
        today = datetime.now(timezone.utc)
        start = today - timedelta(days=364)
        raw = JournalEntryModel.get_sentiments_by_date(user_id, start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
        from collections import defaultdict
        from dateutil.relativedelta import relativedelta
        grouped = defaultdict(list)
        for e in raw:
            key = e["timestamp"].strftime("%Y-%m")  # e.g., '2025-06'
            grouped[key].append(e["sentiment_score"])
        results = []
        for i in range(12):
            key = (start + relativedelta(months=i)).strftime('%Y-%m')
            avg = sum(grouped.get(key, [])) / len(grouped[key]) if grouped.get(key) else 0
            results.append({
                "month": datetime.strptime(key, "%Y-%m").strftime("Month of %B"),
                "average_sentiment": avg
            })
        return results

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

    @staticmethod
    def semantic_search_entries(user_id, query):
        print("we enter service method for sure right?")
        query_vector = TextAnalysisService.generate_openai_embedding(query)

        return JournalEntryModel.get_entries_by_semantic_search(user_id, query_vector)

    def get_top_keywords(user_id, top_n=10):
        try:
            entries = db_session.query(JournalEntryModel.keywords).filter_by(user_id=user_id).all()
            all_keywords = [kw for entry in entries if entry.keywords for kw in entry.keywords]
            return Counter(all_keywords).most_common(top_n)
        except Exception as e:
            print(f"[ERROR] Failed to retrieve top keywords: {e}")
            raise