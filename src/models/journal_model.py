import uuid
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from database import get_table
from boto3.dynamodb.conditions import Key, Attr
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from services.text_service import TextAnalysisService


class JournalEntryModel:
    TABLE_NAME = "journals"

    def __init__(self, user_id, entry, sentiment=None, emotions=None, timestamp=None, keywords=None,
                 weather=None, location=None, sentiment_score=None, embedding=None):
        self.user_id = user_id
        if timestamp:
            dt = datetime.fromisoformat(timestamp)
            dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            self.timestamp = dt.astimezone(timezone.utc).isoformat()
        else:
            self.timestamp = datetime.now(timezone.utc).isoformat()

        self.entry_id = str(uuid.uuid4())
        self.entry = entry
        self.sentiment = sentiment
        self.emotions = emotions
        self.keywords = keywords
        self.weather = weather
        self.location = location
        self.sentiment_score = str(sentiment_score)
        self.embedding = embedding

    def save(self):
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
            return self
        except Exception as e:
            print(f"[ERROR] Failed to save journal entry: {e}")
            raise

    def to_dict(self):
        return self.__dict__

    @classmethod
    def get_entry(cls, user_id, timestamp):
        try:
            journals_table = get_table(cls.TABLE_NAME)
            response = journals_table.get_item(Key={"user_id": user_id, "timestamp": timestamp})
            return response.get("Item")
        except Exception as e:
            print(f"[ERROR] Failed to retrieve journal entry: {e}")
            raise

   
    @classmethod
    def delete_entry(cls, entry_id):
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
            journals_table.delete_item(Key={"user_id": item["user_id"], "timestamp": item["timestamp"]})
            return True
        except Exception as e:
            print(f"[ERROR] Failed to delete journal entry: {e}")
            raise

  

    @classmethod
    def get_entries_by_month(cls, user_id, year, month):
        try:
            journals_table = get_table(cls.TABLE_NAME)

            start_date = datetime(int(year), int(month), 1, tzinfo=timezone.utc)
            end_day = monthrange(int(year), int(month))[1]
            end_date = datetime(int(year), int(month), end_day, 23, 59, 59, tzinfo=timezone.utc)

            start_iso = start_date.isoformat()
            end_iso = end_date.isoformat()

            print(f"📅 Querying from {start_iso} to {end_iso} for user {user_id}")

            entries = []
            scan_kwargs = {
                "FilterExpression": Attr("user_id").eq(user_id) & Attr("timestamp").between(start_iso, end_iso)
            }

            while True:
                response = journals_table.scan(**scan_kwargs)
                items = response.get("Items", [])
                entries.extend(items)

                if "LastEvaluatedKey" not in response:
                    break
                scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

            print(f"✅ Found {len(entries)} entries for {year}-{month}")
            return entries

        except Exception as e:
            print(f"[ERROR] Failed to retrieve entries for {year}-{month}: {e}")
            raise

    @classmethod
    def get_all_entries(cls, user_id, limit=None, specific_attributes=None):
        """
        Optimized version: Retrieve all journal entries for a user using pagination.
        
        :param user_id: The user's ID.
        :param limit: Optional limit on total number of entries to return
        :param specific_attributes: List of specific attributes to fetch (e.g., ['timestamp', 'content', 'sentiment_score'])
        :return: A list of all journal entries.
        """
        try:
            table = get_table(cls.TABLE_NAME)
            entries = []
            
            query_kwargs = {
                "KeyConditionExpression": Key("user_id").eq(user_id)
            }
            
            # Optimization 1: Only fetch specific attributes if provided
            if specific_attributes:
                query_kwargs["ProjectionExpression"] = ", ".join(specific_attributes)
            
            # Optimization 2: Set page size for better performance
            # DynamoDB has a 1MB limit per query, so we set a reasonable page size
            query_kwargs["Limit"] = 100  # Adjust based on your average item size
            
            total_fetched = 0
            
            while True:
                response = table.query(**query_kwargs)
                items = response.get("Items", [])
                entries.extend(items)
                
                total_fetched += len(items)
                
                # Optimization 3: Respect the limit parameter
                if limit and total_fetched >= limit:
                    entries = entries[:limit]  # Trim to exact limit
                    break
                    
                if "LastEvaluatedKey" not in response:
                    break
                    
                query_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

            print(f"✅ Retrieved {len(entries)} entries for user {user_id}")
            return entries
            
        except Exception as e:
            print(f"[ERROR] Failed to retrieve all journal entries: {e}")
            raise


    @classmethod
    def get_recent_entries(cls, user_id):
        try:
            journals_table = get_table(cls.TABLE_NAME)
            response = journals_table.query(
                KeyConditionExpression=Key("user_id").eq(user_id),
                ScanIndexForward=False,
                Limit=12
            )
            return response.get("Items", [])
        except Exception as e:
            print(f"[ERROR] Failed to retrieve recent entries: {e}")
            raise


    @classmethod
    def get_entries_by_keyword(cls, user_id, keyword):
        try:
            journals_table = get_table(cls.TABLE_NAME)
            response = journals_table.scan(
                FilterExpression=Attr("user_id").eq(user_id) & Attr("keywords").contains(keyword)
            )
            return response.get("Items", [])
        except Exception as e:
            print(f"[ERROR] Failed to retrieve entries by keyword '{keyword}': {e}")
            raise

    @classmethod
    def get_top_keywords(cls, user_id, top_n=10):
        try:
            journals_table = get_table(cls.TABLE_NAME)
            response = journals_table.query(KeyConditionExpression=Key("user_id").eq(user_id))
            entries = response.get("Items", [])
            all_keywords = [kw for e in entries for kw in e.get("keywords", [])]
            return Counter(all_keywords).most_common(top_n)
        except Exception as e:
            print(f"[ERROR] Failed to retrieve top keywords: {e}")
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

            today = datetime.now(timezone.utc)
            one_year_ago = today - timedelta(days=365)
            start_iso = one_year_ago.isoformat()

            entries = []
            scan_kwargs = {
                "FilterExpression": Attr("user_id").eq(user_id) & Attr("timestamp").gte(start_iso)
            }

            while True:
                response = journals_table.scan(**scan_kwargs)
                items = response.get("Items", [])
                entries.extend(items)

                if "LastEvaluatedKey" not in response:
                    break
                scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

            # Count how many entries per date
            date_counts = Counter(entry["timestamp"][:10] for entry in entries)

            # Prepare heatmap structure (last 365 days)
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
        try:
            table = get_table(cls.TABLE_NAME)
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)

            entries = []
            scan_kwargs = {
                "FilterExpression": Attr("user_id").eq(user_id) &
                                    Attr("timestamp").between(start_dt.isoformat(), end_dt.isoformat())
            }

            while True:
                response = table.scan(**scan_kwargs)
                entries.extend(response.get("Items", []))
                if "LastEvaluatedKey" not in response:
                    break
                scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

            return entries
        except Exception as e:
            print(f"[ERROR] Failed to retrieve entries by date: {e}")
            raise


    @classmethod
    def get_last_week_sentiments(cls, user_id):
        today = datetime.now(timezone.utc)
        last_week = today - timedelta(days=6)
        raw = cls.get_sentiments_by_date(user_id, last_week.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))

        grouped = defaultdict(list)
        for e in raw:
            day = e["timestamp"][:10]
            grouped[day].append(float(e["sentiment_score"]))

        return [
            {
                "day": (last_week + timedelta(days=i)).strftime('%A'),
                "average_sentiment": sum(grouped.get((last_week + timedelta(days=i)).strftime('%Y-%m-%d'), [])) /
                                    max(len(grouped.get((last_week + timedelta(days=i)).strftime('%Y-%m-%d'), [])), 1)
            }
            for i in range(7)
        ]

    @classmethod
    def get_last_month_sentiments(cls, user_id):
        today = datetime.now(timezone.utc)
        last_month = today - timedelta(days=29)
        raw = cls.get_sentiments_by_date(user_id, last_month.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))

        grouped = defaultdict(list)
        for e in raw:
            try:
                date = datetime.fromisoformat(e["timestamp"])
            except ValueError:
                continue  # skip if malformed

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

            grouped[label].append(float(e["sentiment_score"]))

        labels = ["4 weeks ago", "3 weeks ago", "2 weeks ago", "Last week", "This week"]
        return [
            {
                "week_label": label,
                "average_sentiment": sum(grouped[label]) / len(grouped[label]) if grouped[label] else 0
            }
            for label in labels
        ]


    @classmethod
    def get_last_year_sentiments(cls, user_id):
        today = datetime.now(timezone.utc)
        one_year_ago = today - timedelta(days=364)
        raw = cls.get_sentiments_by_date(user_id, one_year_ago.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))

        grouped = defaultdict(list)
        for e in raw:
            key = e["timestamp"][:7]  # YYYY-MM
            grouped[key].append(float(e["sentiment_score"]))

        results = []
        for i in range(12):
            key = (one_year_ago + relativedelta(months=i)).strftime('%Y-%m')
            avg = sum(grouped.get(key, [])) / len(grouped.get(key, [])) if grouped.get(key) else 0
            results.append({
                "month": datetime.strptime(key, "%Y-%m").strftime("Month of %B"),
                "average_sentiment": avg
            })

        return results



    @staticmethod
    def get_entries_by_semantic_search(user_id, query_vector, top_k=5):
     

        entries = JournalEntryModel.get_all_entries(user_id)
        def cosine_similarity(v1, v2):
            dot = sum(a * b for a, b in zip(v1, v2))
            norm1 = sum(a * a for a in v1) ** 0.5
            norm2 = sum(b * b for b in v2) ** 0.5
            return dot / (norm1 * norm2) if norm1 and norm2 else 0

        scored = []
        for e in entries:
            if "embedding" in e:
                embedding = [float(x) for x in e["embedding"]]
                sim = cosine_similarity(query_vector, embedding)
                scored.append((sim, e))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [entry for _, entry in scored[:top_k]]