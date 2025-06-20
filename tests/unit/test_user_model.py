import unittest
from unittest.mock import patch, MagicMock
from src.models.user_model import User
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound


class TestUserModel(unittest.TestCase):

    @patch('src.models.user_model.db_session')
    def test_save_new_user(self, mock_db_session):
        """Test saving a new user successfully."""
        # Arrange
        user_id = "test_user_123"
        email = "test@example.com"
        name = "Test User"
        
        # Act
        result = User.save(user_id, email, name)
        
        # Assert
        mock_db_session.merge.assert_called_once()
        mock_db_session.commit.assert_called_once()
        
        # Check that the returned user has correct attributes
        self.assertEqual(result.user_id, user_id)
        self.assertEqual(result.email, email)
        self.assertEqual(result.name, name)

    @patch('src.models.user_model.db_session')
    def test_save_existing_user(self, mock_db_session):
        """Test saving an existing user (update scenario)."""
        # Arrange
        user_id = "existing_user_123"
        email = "updated@example.com"
        name = "Updated User"
        
        # Act
        result = User.save(user_id, email, name)
        
        # Assert
        mock_db_session.merge.assert_called_once()
        mock_db_session.commit.assert_called_once()
        self.assertEqual(result.user_id, user_id)
        self.assertEqual(result.email, email)
        self.assertEqual(result.name, name)

    @patch('src.models.user_model.db_session')
    def test_save_user_database_error(self, mock_db_session):
        """Test handling database errors during user save."""
        # Arrange
        mock_db_session.merge.side_effect = IntegrityError("Duplicate email", None, None)
        
        # Act & Assert
        with self.assertRaises(IntegrityError):
            User.save("test_user", "test@example.com", "Test User")

    @patch('src.models.user_model.db_session')
    def test_find_by_google_id_success(self, mock_db_session):
        """Test finding user by Google ID successfully."""
        # Arrange
        mock_user = MagicMock()
        mock_user.user_id = "google_user_123"
        mock_user.email = "google@example.com"
        mock_user.name = "Google User"
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = mock_user
        mock_db_session.query.return_value = mock_query
        
        # Act
        result = User.find_by_google_id("google_user_123")
        
        # Assert
        mock_db_session.query.assert_called_once_with(User)
        mock_query.filter_by.assert_called_once_with(user_id="google_user_123")
        self.assertEqual(result, mock_user)

    @patch('src.models.user_model.db_session')
    def test_find_by_google_id_not_found(self, mock_db_session):
        """Test finding user by Google ID when user doesn't exist."""
        # Arrange
        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        # Act
        result = User.find_by_google_id("nonexistent_user")
        
        # Assert
        mock_db_session.query.assert_called_once_with(User)
        mock_query.filter_by.assert_called_once_with(user_id="nonexistent_user")
        self.assertIsNone(result)

    @patch('src.models.user_model.db_session')
    def test_find_by_google_id_database_error(self, mock_db_session):
        """Test handling database errors during user lookup."""
        # Arrange
        mock_db_session.query.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with self.assertRaises(Exception):
            User.find_by_google_id("test_user")

    def test_user_model_attributes(self):
        """Test that User model has correct attributes."""
        # Test that the model has the expected columns
        self.assertTrue(hasattr(User, '__tablename__'))
        self.assertEqual(User.__tablename__, 'users')
        
        # Test that the model has the expected relationships
        self.assertTrue(hasattr(User, 'entries'))

    @patch('src.models.user_model.db_session')
    def test_user_save_with_empty_fields(self, mock_db_session):
        """Test saving user with empty or None fields."""
        # Act & Assert - should handle empty strings
        result = User.save("user123", "", "")
        self.assertEqual(result.user_id, "user123")
        self.assertEqual(result.email, "")
        self.assertEqual(result.name, "")

    @patch('src.models.user_model.db_session')
    def test_user_save_with_special_characters(self, mock_db_session):
        """Test saving user with special characters in name."""
        # Arrange
        user_id = "user_123"
        email = "test@example.com"
        name = "José María O'Connor-Smith"
        
        # Act
        result = User.save(user_id, email, name)
        
        # Assert
        self.assertEqual(result.name, name)
        mock_db_session.merge.assert_called_once()
        mock_db_session.commit.assert_called_once()


# Pytest-style integration tests
def test_user_creation_and_retrieval(db):
    """Test creating a user and then retrieving it."""
    # Create user
    user = User.save("integration_test_user", "integration@test.com", "Integration Test User")
    
    # Retrieve user
    found_user = User.find_by_google_id("integration_test_user")
    
    # Assert
    assert found_user is not None
    assert found_user.user_id == "integration_test_user"
    assert found_user.email == "integration@test.com"
    assert found_user.name == "Integration Test User"


def test_user_update(db):
    """Test updating an existing user."""
    # Create initial user
    user = User.save("update_test_user", "original@test.com", "Original Name")
    
    # Update user
    updated_user = User.save("update_test_user", "updated@test.com", "Updated Name")
    
    # Retrieve and verify
    found_user = User.find_by_google_id("update_test_user")
    
    # Assert
    assert found_user.email == "updated@test.com"
    assert found_user.name == "Updated Name"


def test_multiple_users(db):
    """Test creating and retrieving multiple users."""
    # Create multiple users
    user1 = User.save("user1", "user1@test.com", "User One")
    user2 = User.save("user2", "user2@test.com", "User Two")
    user3 = User.save("user3", "user3@test.com", "User Three")
    
    # Retrieve each user
    found_user1 = User.find_by_google_id("user1")
    found_user2 = User.find_by_google_id("user2")
    found_user3 = User.find_by_google_id("user3")
    
    # Assert
    assert found_user1.email == "user1@test.com"
    assert found_user2.email == "user2@test.com"
    assert found_user3.email == "user3@test.com"


if __name__ == '__main__':
    unittest.main() 