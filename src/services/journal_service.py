from datetime import datetime, timezone
from src.models.journal_model import JournalEntryModel
from dateutil.parser import parse
from src.services.text_service import TextAnalysisService
from src.services.weather_service import WeatherService
from collections import Counter
from datetime import timedelta
import logging

class JournalService:
    @staticmethod
    def create_journal_entry(user_id, entry, ip_address, optional_date=None, location_data=None):
        try:
            import logging
            logger = logging.getLogger("journal_service")
            timestamp = parse(optional_date) if optional_date else datetime.now()
            
            journal_entry = JournalEntryModel(
                user_id=user_id,
                entry=entry,
                timestamp=timestamp.isoformat(),
                processing=True,
                ip_address=ip_address,
                location=location_data if location_data else None,
                sentiment=None,
                sentiment_score=None,
                emotions=None,
                keywords=None,
                weather=None,
                embedding=None,
            )

            saved_entry = journal_entry.save()
            
            from src.tasks.enrich import enrich_journal_entry
            enrich_journal_entry.delay(str(saved_entry.entry_id))

            return saved_entry.to_dict()
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise

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
            return {}
    
    @staticmethod
    def get_dashboard_sentiments(user_id):
        try:
            return {
                "last_week": JournalService.get_last_week_sentiments(user_id),
                "last_month": JournalService.get_last_month_sentiments(user_id),
                "last_year": JournalService.get_last_year_sentiments(user_id)
            }
        except Exception as e:
            print(f"Error getting dashboard sentiments for user {user_id}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "last_week": [],
                "last_month": [],
                "last_year": []
            }

    @staticmethod
    def get_last_week_sentiments(user_id):
        try:
            today = datetime.now(timezone.utc)
            start = today - timedelta(days=6)
            raw = JournalEntryModel.get_sentiments_by_date(user_id, start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
            from collections import defaultdict
            grouped = defaultdict(list)
            for e in raw:
                if e["sentiment_score"] is not None and e["timestamp"] is not None:
                    grouped[e["timestamp"].date().isoformat()].append(e["sentiment_score"])
            return [
                {
                    "day": (start + timedelta(days=i)).strftime('%A'),
                    "average_sentiment": sum(grouped.get((start + timedelta(days=i)).strftime('%Y-%m-%d'), [])) /
                                         max(len(grouped.get((start + timedelta(days=i)).strftime('%Y-%m-%d'), [])), 1)
                }
                for i in range(7)
            ]
        except Exception as e:
            print(f"Error getting last week sentiments: {e}")
            return []

    @staticmethod
    def get_last_month_sentiments(user_id):
        try:
            today = datetime.now(timezone.utc)
            start = today - timedelta(days=29)
            raw = JournalEntryModel.get_sentiments_by_date(user_id, start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
            from collections import defaultdict
            grouped = defaultdict(list)
            for e in raw:
                # Skip entries without valid sentiment scores
                if e["sentiment_score"] is not None and e["timestamp"] is not None:
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
        except Exception as e:
            print(f"Error getting last month sentiments: {e}")
            return []

    @staticmethod
    def get_last_year_sentiments(user_id):
        try:
            today = datetime.now(timezone.utc)
            start = today - timedelta(days=364)
            raw = JournalEntryModel.get_sentiments_by_date(user_id, start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
            from collections import defaultdict
            from dateutil.relativedelta import relativedelta
            grouped = defaultdict(list)
            for e in raw:
                # Skip entries without valid sentiment scores
                if e["sentiment_score"] is not None and e["timestamp"] is not None:
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
        except Exception as e:
            print(f"Error getting last year sentiments: {e}")
            return []

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
        return JournalService.get_top_keywords(user_id, top_n)

    @staticmethod
    def semantic_search_entries(user_id, query):
        service = TextAnalysisService()
        query_vector = service.generate_embedding(query)
        return JournalEntryModel.get_entries_by_semantic_search(user_id, query_vector)

    def get_top_keywords(user_id, top_n=10):
        try:
            entries = JournalEntryModel.get_all_keywords(user_id)
            all_keywords = [kw for entry in entries if entry.keywords for kw in entry.keywords]
            return Counter(all_keywords).most_common(top_n)
        except Exception as e:
            # All print statements removed from this file
            raise


    def get_streak_stats(user_id):
        """
        Computes journaling streak statistics for a given user.
        Returns dates in UTC to ensure consistency across timezones.
        """
        entries = JournalService.get_all_journal_entries(user_id)
        # Ensure we're using UTC for all date calculations
        today = datetime.now(timezone.utc).date()
        unique_dates = StreakService._extract_entry_dates(entries)



        if not unique_dates:
            return StreakService._empty_stats()

        sorted_dates = sorted(unique_dates)
        longest_streak = StreakService._calculate_longest_streak(sorted_dates)
        current_streak = StreakService._calculate_current_streak(today, unique_dates)
     
        
        missed_days = StreakService._get_missed_days(today, unique_dates)
        calendar_activity = StreakService._get_calendar_activity(user_id, today, days=30)

        last_entry = max(unique_dates)

        last_entry_with_time = datetime.combine(last_entry, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        return {
            "streak": current_streak,
            "longest_streak": longest_streak,
            "has_written_today": today in unique_dates,
            "last_entry_date": last_entry_with_time.isoformat(),
            "missed_days": missed_days,
            "calendar_activity": calendar_activity
        }


class StreakService:
    @staticmethod
    def _extract_entry_dates(entries):
        """Parses timestamps and returns a set of unique UTC dates."""
        date_set = set()
        debug_dates = []
        for entry in entries:
            try:
                entry_date = parse(entry["timestamp"]).astimezone(timezone.utc).date()
                date_set.add(entry_date)
                debug_dates.append((entry["timestamp"], str(entry_date)))
            except Exception as e:
                pass
        
        return date_set


    @staticmethod
    def _calculate_longest_streak(sorted_dates):
        """Calculates the longest consecutive streak."""
        if not sorted_dates:
            return 0

        longest = current = 1
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                current += 1
                longest = max(longest, current)
            else:
                current = 1
        return longest


    @staticmethod
    def _calculate_current_streak(today, date_set):
        """Calculates current streak ending today."""
        if not date_set:
            return 0

        last_entry_date = max(date_set)
        
        # If the last entry is not from today or yesterday, there is no current streak
        if (today - last_entry_date).days > 1:
            return 0
            
        streak = 0
        cursor = last_entry_date
        
        while cursor in date_set:
            streak += 1
            cursor -= timedelta(days=1)
            
        return streak


    @staticmethod
    def _get_calendar_activity(user_id, today, days):
        """Returns a heatmap-style dictionary of writing activity."""
        heatmap = JournalService.get_heatmap_data(user_id)
        return {
            (today - timedelta(days=i)).isoformat(): heatmap.get((today - timedelta(days=i)).isoformat(), 0) > 0
            for i in range(days)
        }


    @staticmethod
    def _empty_stats():
        """Returns a default zeroed-out stats object."""
        return {
            "streak": 0,
            "longest_streak": 0,
            "has_written_today": False,
            "last_entry_date": None,
            "missed_days": [],
            "calendar_activity": {}
        }

    @staticmethod
    def _get_missed_days(today, date_set):
        """Returns list of ISO dates missed in the last 7 days."""
        missed = []
        for i in range(7):  
            check_date = today - timedelta(days=i)
            if check_date not in date_set:
                missed.append(check_date.isoformat())
        return missed
    