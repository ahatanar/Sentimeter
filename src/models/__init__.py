from src.models.user_model import User
from src.models.journal_model import JournalEntryModel

# Ensure both models are loaded before setting up relationships
User.entries.property.mapper.class_ = JournalEntryModel
JournalEntryModel.user.property.mapper.class_ = User

__all__ = ["User", "JournalEntryModel"]