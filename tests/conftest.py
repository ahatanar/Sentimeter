import pytest
from unittest.mock import patch, MagicMock
from src.app import create_app
from src.database import Base, engine, db_session
from src.models.user_model import User
from src.models.journal_model import JournalEntryModel


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "DATABASE_URL": "sqlite:///:memory:",  # Use in-memory SQLite for testing
        }
    )
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def db():
    """Create a fresh database for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield db_session
    # Clean up after test
    db_session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_user(db):
    """Create a sample user for testing."""
    user = User(user_id="test_user_123", email="test@example.com", name="Test User")
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def sample_journal_entry(db, sample_user):
    """Create a sample journal entry for testing."""
    entry = JournalEntryModel(
        user_id=sample_user.user_id,
        entry="This is a test journal entry",
        sentiment="positive",
        sentiment_score=0.8,
        keywords=["test", "journal"],
        weather={"description": "sunny"},
        location={"city": "Toronto"}
    )
    db.add(entry)
    db.commit()
    return entry