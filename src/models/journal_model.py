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
from src.database import Base, db
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
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Failed to save journal entry: {e}")
            raise

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
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
            return db.session.query(JournalEntryModel).filter_by(user_id=user_id, timestamp=timestamp).one()
        except NoResultFound:
    
            return None
        except Exception as e:
            print(f"[ERROR] Failed to retrieve journal entry: {e}")
            raise

    @classmethod
    def delete_entry(cls, entry_id):
        try:
            entry = db.session.query(JournalEntryModel).filter_by(entry_id=entry_id).one()
            db.session.delete(entry)
            db.session.commit()
            return True
        except NoResultFound:
    
            return False
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Failed to delete journal entry: {e}")
            raise

    @classmethod
    def get_entries_by_month(cls, user_id, year, month, specific_columns=None):
        try:
            start_date = datetime(int(year), int(month), 1, tzinfo=timezone.utc)
            end_day = monthrange(int(year), int(month))[1]
            end_date = datetime(int(year), int(month), end_day, 23, 59, 59, tzinfo=timezone.utc)

            print(f"📅 Querying {user_id} from {start_date} to {end_date}")

            query = db.session.query(JournalEntryModel).filter(
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
            query = db.session.query(JournalEntryModel).filter(
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
            return [entry.to_dict() for entry in db.session.query(JournalEntryModel)
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
            return [entry.to_dict() for entry in db.session.query(JournalEntryModel)
            .filter(JournalEntryModel.user_id == user_id)
            .filter(JournalEntryModel.keywords.any(keyword))
            .all()]
        except Exception as e:
            print(f"[ERROR] Failed to retrieve entries by keyword '{keyword}': {e}")
            raise

   



    @staticmethod
    def get_sentiments_by_date(user_id, start_date, end_date):
        """
        Returns list of entries (with timestamp and sentiment_score) for a user between two dates (inclusive).
        """
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)

            entries = db.session.query(JournalEntryModel.timestamp, JournalEntryModel.sentiment_score) \
                .filter(JournalEntryModel.user_id == user_id) \
                .filter(JournalEntryModel.timestamp >= start_dt) \
                .filter(JournalEntryModel.timestamp < end_dt) \
                .all()

            return [{"timestamp": e.timestamp, "sentiment_score": e.sentiment_score} for e in entries]
        except Exception as e:
            print(f"[ERROR] Failed to retrieve entries by date: {e}")
            raise



    @staticmethod
    def get_entries_by_semantic_search(user_id, query_vector, top_k=5):
        try:
            if not isinstance(query_vector, list):
                raise ValueError("Query vector must be a list of floats")

            results = db.session.query(JournalEntryModel) \
                .filter(JournalEntryModel.user_id == user_id) \
                .filter(JournalEntryModel.embedding != None) \
                .order_by(JournalEntryModel.embedding.cosine_distance(cast(query_vector, Vector(1536)))) \
                .limit(top_k) \
                .all()

            return [entry.to_dict() for entry in results]

        except Exception as e:
            print(f"[ERROR] Failed to perform semantic search: {e}")
            raise

    @staticmethod
    def get_entry_timestamps_in_range(user_id, start_date, end_date):
        """
        Return a list of timestamps for a user between start_date and end_date (inclusive).
        """
        try:
            return [
                entry.timestamp
                for entry in db.session.query(JournalEntryModel.timestamp)
                    .filter(JournalEntryModel.user_id == user_id)
                    .filter(JournalEntryModel.timestamp >= start_date)
                    .filter(JournalEntryModel.timestamp <= end_date)
                    .all()
            ]
        except Exception as e:
            print(f"[ERROR] Failed to fetch entry timestamps for heatmap: {e}")
            return []

    @staticmethod
    def get_all_keywords(user_id):
        try:
            entries = db.session.query(JournalEntryModel.keywords).filter_by(user_id=user_id).all()
            return entries
        except Exception as e:
            print(f"[ERROR] Failed to retrieve all keywords: {e}")
            raise