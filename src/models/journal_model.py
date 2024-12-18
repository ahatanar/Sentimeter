import uuid
from datetime import datetime
from src.database import get_table
import boto3
from boto3.dynamodb.conditions import Key
from collections import Counter
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta
from collections import defaultdict
from collections import OrderedDict
from dateutil.relativedelta import relativedelta

class JournalEntryModel:
    TABLE_NAME = "journals"

    def __init__(self, user_id, entry, sentiment=None, emotions=None, timestamp=None,keywords=None,weather=None,location=None,sentiment_score=None):
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
        self.keywords = keywords
        self.weather = weather
        self.location = location
        self.sentiment_score = str(sentiment_score)
    def save(self):
        """
        Save the journal entry to DynamoDB and return the entry instance.
        :return: The current instance of JournalEntryModel.
        """
        try:
           
            item = {
                "user_id": self.user_id,
                "timestamp": self.timestamp,
                "entry_id": self.entry_id,
                "entry": self.entry,
                "sentiment": self.sentiment,
                "emotions": self.emotions,
                "keywords": self.keywords,
                "weather": self.weather,
                "location": self.location,
                "sentiment_score": self.sentiment_score,
            }

            

            journals_table = get_table(self.TABLE_NAME)
            journals_table.put_item(Item=item)

            print(f"[DEBUG] Successfully saved journal entry: {self.entry_id}")
            return self

        except Exception as e:
            print(f"[ERROR] Failed to save journal entry: {e}")
            raise
    def to_dict(self):
        """
        Return all attributes of the model as a dictionary.
        """
        return self.__dict__
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
        print("user_id:", user_id)
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
    def delete_entry(cls, entry_id):
        """
        Delete a journal entry using entry_id.
        """
        try:
            journals_table = get_table(cls.TABLE_NAME)

            response = journals_table.query(
                IndexName="entry_id-index",  
                KeyConditionExpression=Key("entry_id").eq(entry_id)
            )

            if not response["Items"]:
                print(f"[DEBUG] No journal entry found with entry_id: {entry_id}")
                return False

            item = response["Items"][0]
            user_id = item["user_id"]
            timestamp = item["timestamp"]

            journals_table.delete_item(
                Key={"user_id": user_id, "timestamp": timestamp}
            )
            print(f"[DEBUG] Deleted journal entry with entry_id: {entry_id}")
            return True

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
        Retrieve the last 12 journal entries for a user.
        :param user_id: The user's ID.
        :return: A list of the 12 most recent journal entries.
        """
        try:
            journals_table = get_table(cls.TABLE_NAME)
            response = journals_table.query(
                KeyConditionExpression=Key("user_id").eq(user_id),
                ScanIndexForward=False, 
                Limit=12
            )
            entries = response.get("Items", [])
            print(f"[DEBUG] Retrieved last 12 entries for user {user_id}: {entries}")
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

            date_counts = Counter(entry["timestamp"][:10] for entry in entries)  

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
        Retrieve entries filtered by a date range, including all timestamps within the end date.
        """
        try:
            journals_table = get_table(cls.TABLE_NAME)

            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

            start_date_str = start_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")
            end_date_str = end_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")

            print(f"[DEBUG] Querying entries for user_id={user_id} between {start_date_str} and {end_date_str}")

            response = journals_table.scan(
                FilterExpression=Attr("user_id").eq(user_id) &
                                Attr("timestamp").between(start_date_str, end_date_str)
            )
            
            entries = response.get("Items", [])
            print(f"[DEBUG] Retrieved {len(entries)} entries for user_id={user_id} between {start_date_str} and {end_date_str}")
            
            return entries
        except Exception as e:
            print(f"[ERROR] Failed to retrieve entries by date: {e}")
            raise

    @classmethod
    def get_last_week_sentiments(cls, user_id):
        today = datetime.now()
        last_week = today - timedelta(days=6)
        
        raw_sentiments = cls.get_sentiments_by_date(
            user_id,
            last_week.strftime('%Y-%m-%d'),
            today.strftime('%Y-%m-%d'),
        )
        
        daily_sentiments = defaultdict(list)
        for entry in raw_sentiments:
            date = entry["timestamp"][:10]  
            sentiment = float(entry["sentiment_score"])
            daily_sentiments[date].append(sentiment)
        
        averages = {
            date: sum(scores) / len(scores) for date, scores in daily_sentiments.items()
        }
        
        week_data = []
        for i in range(7):
            day = last_week + timedelta(days=i)
            formatted_day = day.strftime('%A')
            week_data.append({
                "day": formatted_day,
                "average_sentiment": averages.get(day.strftime('%Y-%m-%d'), 0)
            })
        
        print(week_data)
        return week_data

    @classmethod
    def get_last_month_sentiments(cls, user_id):
        today = datetime.now()
        last_month = today - timedelta(days=29)
        
        raw_sentiments = cls.get_sentiments_by_date(
            user_id,
            last_month.strftime('%Y-%m-%d'),
            today.strftime('%Y-%m-%d'),
        )
        
        weekly_sentiments = defaultdict(list)
        for entry in raw_sentiments:
            date = datetime.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%S.%f")
            days_ago = (today - date).days
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
            sentiment = float(entry["sentiment_score"])
            weekly_sentiments[label].append(sentiment)
        
        averages = {
            label: sum(scores) / len(scores) for label, scores in weekly_sentiments.items()
        }
        
        labels = ["4 weeks ago", "3 weeks ago", "2 weeks ago", "Last week", "This week"]
        week_data = [{"week_label": label, "average_sentiment": averages.get(label, 0)} for label in labels]
        
        print(week_data)
        return week_data

    @classmethod
    def get_last_year_sentiments(cls, user_id):
        today = datetime.now()
        last_year = today - timedelta(days=364)
        
        raw_sentiments = cls.get_sentiments_by_date(
            user_id,
            last_year.strftime('%Y-%m-%d'),
            today.strftime('%Y-%m-%d'),
        )
        
        monthly_sentiments = defaultdict(list)
        for entry in raw_sentiments:
            month = entry["timestamp"][:7] 
            sentiment = float(entry["sentiment_score"])
            monthly_sentiments[month].append(sentiment)
        
        averages = {
            month: sum(scores) / len(scores) for month, scores in monthly_sentiments.items()
        }
        
        for i in range(12):
            month_date = (last_year + relativedelta(months=i))
            month_key = month_date.strftime('%Y-%m') 
            if month_key not in averages:
                averages[month_key] = 0
        
        month_data = [
            {
                "month": datetime.strptime(month, "%Y-%m").strftime("Month of %B"),
                "average_sentiment": avg
            }
            for month, avg in sorted(averages.items(), key=lambda x: datetime.strptime(x[0], "%Y-%m"))
        ]
        
        print(month_data)
        return month_data