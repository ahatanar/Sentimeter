import uuid
from datetime import datetime
from src.database import get_table
import boto3
from boto3.dynamodb.conditions import Key
from collections import Counter
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta

class JournalEntryModel:
    TABLE_NAME = "journals"

    def __init__(self, user_id, entry, sentiment=None, emotions=None, timestamp=None,):
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
    @classmethod
    def get_entries_by_keyword(cls, user_id, keyword):
        """
        Retrieve all journal entries for a user that contain a specific keyword.
        :param user_id: The user's ID.
        :param keyword: The keyword to filter by.
        :return: A list of journal entries matching the keyword.
        """
        try:
            journals_table = get_table(cls.TABLE_NAME)
            response = journals_table.scan(
                FilterExpression=Attr("user_id").eq(user_id) & Attr("keywords").contains(keyword)
            )
            entries = response.get("Items", [])
            print(f"[DEBUG] Retrieved entries with keyword '{keyword}' for user {user_id}: {entries}")
            return entries
        except Exception as e:
            print(f"[ERROR] Failed to retrieve entries by keyword '{keyword}': {e}")
            raise

    @classmethod
    def get_top_keywords(cls, user_id, top_n=10):
        """
        Retrieve the top N most common keywords across all entries for a user.
        :param user_id: The user's ID.
        :param top_n: The number of top keywords to return.
        :return: A list of tuples [(keyword, count), ...].
        """
        try:
            journals_table = get_table(cls.TABLE_NAME)
            response = journals_table.query(
                KeyConditionExpression=Key("user_id").eq(user_id)
            )
            entries = response.get("Items", [])
            
            all_keywords = [keyword for entry in entries for keyword in entry.get("keywords", [])]

            keyword_counts = Counter(all_keywords)

            top_keywords = keyword_counts.most_common(top_n)
            print(f"[DEBUG] Top {top_n} keywords for user {user_id}: {top_keywords}")
            return top_keywords
        except Exception as e:
            print(f"[ERROR] Failed to retrieve top keywords for user {user_id}: {e}")
            raise

    @classmethod
    def get_recent_entries(cls, user_id):
        """
        Retrieve the last 10 journal entries for a user.
        :param user_id: The user's ID.
        :return: A list of the 10 most recent journal entries.
        """
        try:
            journals_table = get_table(cls.TABLE_NAME)
            response = journals_table.query(
                KeyConditionExpression=Key("user_id").eq(user_id),
                ScanIndexForward=False, 
                Limit=10  
            )
            entries = response.get("Items", [])
            print(f"[DEBUG] Retrieved last 10 entries for user {user_id}: {entries}")
            return entries
        except Exception as e:
            print(f"[ERROR] Failed to retrieve recent entries: {e}")
            raise

    @classmethod
    def get_entries_by_month(cls, user_id, year, month):
        """
        Retrieve journal entries for a user filtered by a specific year and month.
        :param user_id: The user's ID.
        :param year: The year to filter by (e.g., 2024).
        :param month: The month to filter by (e.g., 11 for November).
        :return: A list of journal entries matching the criteria.
        """
        try:
            journals_table = get_table(cls.TABLE_NAME)
            prefix = f"{year}-{int(month):02}"
            response = journals_table.scan(
                FilterExpression=Attr("user_id").eq(user_id) &
                                Attr("timestamp").begins_with(prefix)
            )
            entries = response.get("Items", [])
            print(f"[DEBUG] Retrieved entries for {year}-{month} for user {user_id}: {entries}")
            return entries
        except Exception as e:
            print(f"[ERROR] Failed to retrieve entries for {year}-{month}: {e}")
            raise
    @classmethod
    def get_heatmap_data(cls, user_id):
        """
        Retrieve heatmap data for the last 365 days, grouped by date.
        :param user_id: The user's ID.
        :return: A dictionary with dates as keys and entry counts as values.
        """
        try:
            journals_table = get_table(cls.TABLE_NAME)

            today = datetime.now()
            one_year_ago = today - timedelta(days=365)
            date_filter = one_year_ago.strftime('%Y-%m-%d')

            response = journals_table.scan(
                FilterExpression=Key("user_id").eq(user_id) & Attr("timestamp").gte(date_filter)
            )

            entries = response.get("Items", [])
            print(f"[DEBUG] Retrieved {len(entries)} entries for user {user_id} in the last 365 days.")

            date_counts = Counter(entry["timestamp"][:10] for entry in entries)  # Extract only the date (YYYY-MM-DD)

            heatmap_data = {}
            for i in range(365):
                date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
                heatmap_data[date] = date_counts.get(date, 0)

            return heatmap_data
        except Exception as e:
            print(f"[ERROR] Failed to retrieve heatmap data: {e}")
            raise


    @classmethod
    def get_sentiments_by_date(cls, user_id, start_date, end_date):
        """
        Retrieve sentiment data grouped by date within a specific date range.
        :param user_id: The user's ID.
        :param start_date: Start date (YYYY-MM-DD).
        :param end_date: End date (YYYY-MM-DD).
        :return: A dictionary with dates as keys and sentiment scores as values.
        """
        try:
            journals_table = get_table(cls.TABLE_NAME)

            response = journals_table.scan(
                FilterExpression=Attr("user_id").eq(user_id) &
                                Attr("timestamp").between(start_date, end_date)
            )

            entries = response.get("Items", [])
            print(f"[DEBUG] Retrieved {len(entries)} entries for user {user_id} between {start_date} and {end_date}")

            sentiments = {}
            for entry in entries:
                date = entry["timestamp"][:10]  
                score = 1 if entry["sentiment"] == "positive" else -1 if entry["sentiment"] == "negative" else 0
                sentiments.setdefault(date, []).append(score)

            averaged_sentiments = {date: sum(scores) / len(scores) for date, scores in sentiments.items()}
            return averaged_sentiments
        except Exception as e:
            print(f"[ERROR] Failed to retrieve sentiments by date: {e}")
            raise

    @classmethod
    def get_last_week_sentiments(cls, user_id):
        """
        Retrieve sentiment data for the last week, aggregated by day.
        :param user_id: The user's ID.
        :return: A dictionary with dates as keys and average sentiment scores as values.
        """
        today = datetime.now()
        last_week = today - timedelta(days=7)
        sentiments = cls.get_sentiments_by_date(user_id, last_week.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
        return {date: score for date, score in sorted(sentiments.items())}

    @classmethod
    def get_last_month_sentiments(cls, user_id):
        """
        Retrieve sentiment data for the last month, aggregated by week.
        :param user_id: The user's ID.
        :return: A dictionary with weeks as keys (e.g., "week_46") and average sentiment scores as values.
        """
        today = datetime.now()
        last_month = today - timedelta(days=30)
        sentiments = cls.get_sentiments_by_date(user_id, last_month.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))

        from collections import defaultdict
        weekly_sentiments = defaultdict(list)
        for date, score in sentiments.items():
            week = datetime.strptime(date, "%Y-%m-%d").isocalendar()[1]  
            weekly_sentiments[week].append(score)

        return {f"week_{week}": sum(scores) / len(scores) for week, scores in weekly_sentiments.items()}

    @classmethod
    def get_last_year_sentiments(cls, user_id):
        """
        Retrieve sentiment data for the last year, aggregated by month.
        :param user_id: The user's ID.
        :return: A dictionary with months as keys (e.g., "2024-11") and average sentiment scores as values.
        """
        today = datetime.now()
        last_year = today - timedelta(days=365)
        sentiments = cls.get_sentiments_by_date(user_id, last_year.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))

        from collections import defaultdict
        monthly_sentiments = defaultdict(list)
        for date, score in sentiments.items():
            month = date[:7]  
            monthly_sentiments[month].append(score)

        return {month: sum(scores) / len(scores) for month, scores in monthly_sentiments.items()}