from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from src.database import Base, db


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    entries = relationship("JournalEntryModel", back_populates="user", lazy="dynamic")
    notification_settings = relationship("NotificationSettings", back_populates="user", uselist=False)

    @classmethod
    def save(cls, user_id, email, name):
        user = cls(user_id=user_id, email=email, name=name)
        db.session.merge(user)
        db.session.commit()
        return user

    @classmethod
    def find_by_google_id(cls, google_id):
        return db.session.query(cls).filter_by(user_id=google_id).first()
