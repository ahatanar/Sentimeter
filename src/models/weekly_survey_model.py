from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from datetime import date
from src.database import Base, db


class WeeklySurvey(Base):
    __tablename__ = "weekly_surveys"

    # composite PK prevents duplicate week rows
    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    week_start = Column(Date, primary_key=True)  # Monday of the week (calendar-week, not ISO number)

    # 1–5 Likert scales
    stress = Column(Integer, nullable=False)
    anxiety = Column(Integer, nullable=False)
    depression = Column(Integer, nullable=False)
    happiness = Column(Integer, nullable=False)
    satisfaction = Column(Integer, nullable=False)

    # high-signal booleans
    self_harm_thoughts = Column(Boolean, default=False)
    significant_sleep_issues = Column(Boolean, default=False)

    urgent_flag = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    def compute_urgent_flag(self):
        """Apply tiered safety logic."""
        if self.self_harm_thoughts:
            return True
        if max(self.depression, self.anxiety) >= 4:
            return True
        # rolling stress streak handled in service layer (for future implementation)
        return False

    @classmethod
    def create_survey(cls, user_id: str, week_start: date, **survey_data):
        """Create a new weekly survey"""
        survey = cls(
            user_id=user_id,
            week_start=week_start,
            **survey_data
        )
        survey.urgent_flag = survey.compute_urgent_flag()
        db.session.add(survey)
        db.session.commit()
        return survey

    @classmethod
    def find_by_user_and_week(cls, user_id: str, week_start: date):
        """Find survey for specific user and week"""
        return db.session.query(cls).filter_by(
            user_id=user_id,
            week_start=week_start
        ).first()

    @classmethod
    def get_user_surveys(cls, user_id: str, limit: int = None):
        """Get surveys for user, ordered by week_start descending"""
        query = db.session.query(cls).filter_by(user_id=user_id).order_by(cls.week_start.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

    @classmethod
    def get_user_surveys_since(cls, user_id: str, since_date: date):
        """Get surveys for user since specific date"""
        return db.session.query(cls).filter_by(user_id=user_id).filter(
            cls.week_start >= since_date
        ).order_by(cls.week_start.asc()).all() 