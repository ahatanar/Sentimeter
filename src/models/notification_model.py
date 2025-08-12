from sqlalchemy import Column, String, Boolean, DateTime, Time, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import time, datetime, timezone
from src.database import Base, db


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    journal_enabled = Column(Boolean, default=False, nullable=False)
    journal_frequency = Column(String, default="daily", nullable=False)
    journal_time = Column(Time, default=time(20, 0), nullable=False)
    journal_day = Column(String, default="monday", nullable=False)
    survey_enabled = Column(Boolean, default=True, nullable=False)
    survey_day = Column(String, default="sunday", nullable=False)   # lowercase weekday
    survey_time = Column(Time, default=time(18, 0), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="notification_settings")

    @classmethod
    def create_default_settings(cls, user_id):
        settings = cls(
            user_id=user_id,
            journal_enabled=False,
            journal_frequency="daily",
            journal_time=time(20, 0),
            journal_day="monday",
            survey_enabled=True,
            survey_day="sunday",
            survey_time=time(18, 0)
        )
        db.session.add(settings)
        db.session.commit()
        return settings

    @classmethod
    def find_by_user_id(cls, user_id):
        return db.session.query(cls).filter_by(user_id=user_id).first()

    @classmethod
    def update_settings(cls, user_id, **kwargs):
        settings = cls.find_by_user_id(user_id)
        if not settings:
            settings = cls.create_default_settings(user_id)
        
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        db.session.commit()
        return settings 