import uuid
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from src.services.text_service import TextAnalysisService
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, and_, cast
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from src.database import Base, db_session
from sqlalchemy.sql.expression import desc

from pgvector.sqlalchemy import Vector

class JournalEntryModel(Base):
    __tablename__ = "journals"

    entry_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    entry = Column(String, nullable=False)
    sentiment = Column(String)
    sentiment_score = Column(Float)
    emotions = Column(JSON)
    keywords = Column(ARRAY(String))
    weather = Column(JSON)
    location = Column(JSON)
    embedding = Column(Vector(1536))

    user = relationship("User", back_populates="entries", lazy="joined")


    def save(self):
        try:
            db_session.add(self)
            db_session.commit()
            return self
        except Exception as e:
            db_session.rollback()
            print(f"[ERROR] Failed to save journal entry: {e}")
            raise

    def delete(self):
        try:
            db_session.delete(self)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            print(f"[ERROR] Failed to delete journal entry: {e}")
            raise

    def to_dict(self):
        return {
            "entry_id": str(self.entry_id),
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "entry": self.entry,
            "sentiment": self.sentiment,
            "sentiment_score": self.sentiment_score,
            "emotions": self.emotions,
            "keywords": self.keywords,
            "weather": self.weather,
            "location": self.location
        }

    @classmethod
    def get_entry(cls, user_id, timestamp):
        try:
            return db_session.query(JournalEntryModel).filter_by(user_id=user_id, timestamp=timestamp).one()
        except NoResultFound:
            print(f"[DEBUG] No journal entry found for user {user_id} at {timestamp}")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to retrieve journal entry: {e}")
            raise

    @classmethod
    def delete_entry(cls, entry_id):
        try:
            entry = db_session.query(JournalEntryModel).filter_by(entry_id=entry_id).one()
            db_session.delete(entry)
            db_session.commit()
            return True
        except NoResultFound:
            print(f"[DEBUG] No journal entry found with entry_id: {entry_id}")
            return False
        except Exception as e:
            db_session.rollback()
            print(f"[ERROR] Failed to delete journal entry: {e}")
            raise

    @classmethod
    def get_entries_by_month(cls, user_id, year, month, specific_columns=None):
        try:
            start_date = datetime(int(year), int(month), 1, tzinfo=timezone.utc)
            end_day = monthrange(int(year), int(month))[1]
            end_date = datetime(int(year), int(month), end_day, 23, 59, 59, tzinfo=timezone.utc)

            print(f"📅 Querying {user_id} from {start_date} to {end_date}")

            query = db_session.query(JournalEntryModel).filter(
                and_(
                    JournalEntryModel.user_id == user_id,
                    JournalEntryModel.timestamp >= start_date,
                    JournalEntryModel.timestamp <= end_date
                )
            )

            results = query.all()
            return [entry.to_dict() if not specific_columns else {
                field: getattr(entry, field) for field in specific_columns
            } for entry in results]

        except Exception as e:
            print(f"[ERROR] Failed to retrieve entries for {year}-{month}: {e}")
            raise

    @classmethod
    def get_all_entries(cls, user_id, limit=None, specific_attributes=None):
        """
        Retrieve all journal entries for a user using PostgreSQL with optional limit and selected attributes.

        :param user_id: The user's ID.
        :param limit: Optional max number of entries to return.
        :param specific_attributes: Optional list of attribute names to return per entry.
        :return: List of entries as dicts.
        """
        try:
            query = db_session.query(JournalEntryModel).filter(
                JournalEntryModel.user_id == user_id
            ).order_by(JournalEntryModel.timestamp.desc())

            if limit:
                query = query.limit(limit)

            entries = query.all()

            if specific_attributes:
                return [
                    {field: getattr(entry, field) for field in specific_attributes}
                    for entry in entries
                ]
            else:
                return [entry.to_dict() for entry in entries]

        except Exception as e:
            print(f"[ERROR] Failed to retrieve entries for user {user_id}: {e}")
            raise

    @staticmethod
    def get_recent_entries(user_id, limit=12):
        try:
            return [entry.to_dict() for entry in db_session.query(JournalEntryModel)
            .filter_by(user_id=user_id)
            .order_by(desc(JournalEntryModel.timestamp))
            .limit(limit)
            .all()]
        except Exception as e:
            print(f"[ERROR] Failed to retrieve recent entries: {e}")
            raise

    @staticmethod
    def get_entries_by_keyword(user_id, keyword):
        try:
            return [entry.to_dict() for entry in db_session.query(JournalEntryModel)
            .filter(JournalEntryModel.user_id == user_id)
            .filter(JournalEntryModel.keywords.any(keyword))
            .all()]
        except Exception as e:
            print(f"[ERROR] Failed to retrieve entries by keyword '{keyword}': {e}")
            raise

    def get_top_keywords(user_id, top_n=10):
        try:
            entries = db_session.query(JournalEntryModel.keywords).filter_by(user_id=user_id).all()
            all_keywords = [kw for entry in entries if entry.keywords for kw in entry.keywords]
            return Counter(all_keywords).most_common(top_n)
        except Exception as e:
            print(f"[ERROR] Failed to retrieve top keywords: {e}")
            raise

    @staticmethod
    def get_heatmap_data(user_id):
        """
        Retrieve heatmap data for the last 365 days, grouped by date.
        :param user_id: The user's ID.
        :return: A dictionary with dates as keys and entry counts as values.
        """
        try:
            today = datetime.now(timezone.utc)
            one_year_ago = today - timedelta(days=365)

            entries = db_session.query(JournalEntryModel.timestamp) \
                .filter(JournalEntryModel.user_id == user_id) \
                .filter(JournalEntryModel.timestamp >= one_year_ago) \
                .all()

            # Count entries per date
            date_counts = Counter(entry.timestamp.date().isoformat() for entry in entries)

            # Generate full 365-day heatmap
            heatmap_data = {
                (today - timedelta(days=i)).strftime('%Y-%m-%d'): date_counts.get(
                    (today - timedelta(days=i)).strftime('%Y-%m-%d'), 0)
                for i in range(365)
            }

            return heatmap_data
        except Exception as e:
            print(f"[ERROR] Failed to retrieve heatmap data: {e}")
            raise

    @staticmethod
    def get_sentiments_by_date(user_id, start_date, end_date):
        """
        Returns list of entries (with timestamp and sentiment_score) for a user between two dates (inclusive).
        """
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)

            entries = db_session.query(JournalEntryModel.timestamp, JournalEntryModel.sentiment_score) \
                .filter(JournalEntryModel.user_id == user_id) \
                .filter(JournalEntryModel.timestamp >= start_dt) \
                .filter(JournalEntryModel.timestamp < end_dt) \
                .all()

            return [{"timestamp": e.timestamp, "sentiment_score": e.sentiment_score} for e in entries]
        except Exception as e:
            print(f"[ERROR] Failed to retrieve entries by date: {e}")
            raise

    @staticmethod
    def get_last_week_sentiments(user_id):
        today = datetime.now(timezone.utc)
        start = today - timedelta(days=6)
        raw = JournalEntryModel.get_sentiments_by_date(user_id, start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))

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
    def get_entries_by_semantic_search(user_id, query_vector, top_k=5):
        try:
            if not isinstance(query_vector, list):
                raise ValueError("Query vector must be a list of floats")

            results = db_session.query(JournalEntryModel) \
                .filter(JournalEntryModel.user_id == user_id) \
                .filter(JournalEntryModel.embedding != None) \
                .order_by(JournalEntryModel.embedding.cosine_distance(cast(query_vector, Vector(1536)))) \
                .limit(top_k) \
                .all()

            return [entry.to_dict() for entry in results]

        except Exception as e:
            print(f"[ERROR] Failed to perform semantic search: {e}")
            raise