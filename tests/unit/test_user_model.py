import unittest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import IntegrityError
from src.models.user_model import User


class TestUserModel(unittest.TestCase):

    @patch('src.models.user_model.db.session')
    def test_save_new_user(self, mock_db_session):
        """Test saving a new user successfully."""
        # Arrange
        user_id = "test_user_123"
        email = "test@example.com"
        name = "Test User"
        
        # Act
        user = User.save(user_id, email, name)
        
        # Assert
        self.assertEqual(user.user_id, user_id)
        self.assertEqual(user.email, email)
        self.assertEqual(user.name, name)
        mock_db_session.merge.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @patch('src.models.user_model.db.session')
    def test_save_existing_user(self, mock_db_session):
        """Test saving an existing user (update scenario)."""
        # Arrange
        user_id = "existing_user_123"
        email = "existing@example.com"
        name = "Existing User"
        
        # Act
        user = User.save(user_id, email, name)
        
        # Assert
        self.assertEqual(user.user_id, user_id)
        self.assertEqual(user.email, email)
        self.assertEqual(user.name, name)
        mock_db_session.merge.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @patch('src.models.user_model.db.session')
    def test_save_user_database_error(self, mock_db_session):
        """Test handling database errors during user save."""
        # Arrange
        user_id = "error_user_123"
        email = "error@example.com"
        name = "Error User"
        
        mock_db_session.merge.side_effect = IntegrityError("Duplicate email", None, None)
        
        # Act & Assert
        with self.assertRaises(IntegrityError):
            User.save(user_id, email, name)

    @patch('src.models.user_model.db.session')
    def test_find_by_google_id_success(self, mock_db_session):
        """Test finding user by Google ID successfully."""
        # Arrange
        google_id = "google_user_123"
        expected_user = User(user_id=google_id, email="google@example.com", name="Google User")
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = expected_user
        mock_db_session.query.return_value = mock_query
        
        # Act
        result = User.find_by_google_id(google_id)
        
        # Assert
        self.assertEqual(result, expected_user)
        mock_db_session.query.assert_called_once_with(User)

    @patch('src.models.user_model.db.session')
    def test_find_by_google_id_not_found(self, mock_db_session):
        """Test finding user by Google ID when user doesn't exist."""
        # Arrange
        google_id = "nonexistent_user_123"
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        # Act
        result = User.find_by_google_id(google_id)
        
        # Assert
        self.assertIsNone(result)
        mock_db_session.query.assert_called_once_with(User)

    @patch('src.models.user_model.db.session')
    def test_find_by_google_id_database_error(self, mock_db_session):
        """Test handling database errors during user lookup."""
        # Arrange
        google_id = "error_user_123"
        
        mock_db_session.query.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with self.assertRaises(Exception):
            User.find_by_google_id(google_id)

    def test_user_model_attributes(self):
        """Test that User model has correct attributes."""
        # Test that the model has the expected columns
        self.assertTrue(hasattr(User, '__tablename__'))
        self.assertEqual(User.__tablename__, 'users')
        
        # Test that the model has the expected relationships
        self.assertTrue(hasattr(User, 'entries'))

    @patch('src.models.user_model.db.session')
    def test_user_save_with_empty_fields(self, mock_db_session):
        """Test saving user with empty or None fields."""
        # Act & Assert - should handle empty strings
        user_id = "empty_user_123"
        email = ""
        name = ""
        
        user = User.save(user_id, email, name)
        
        self.assertEqual(user.user_id, user_id)
        self.assertEqual(user.email, email)
        self.assertEqual(user.name, name)

    @patch('src.models.user_model.db.session')
    def test_user_save_with_special_characters(self, mock_db_session):
        """Test saving user with special characters in name."""
        # Arrange
        user_id = "special_user_123"
        email = "test+tag@example.com"
        name = "José María O'Connor-Smith"
        
        # Act
        user = User.save(user_id, email, name)
        
        # Assert
        self.assertEqual(user.user_id, user_id)
        self.assertEqual(user.email, email)
        self.assertEqual(user.name, name)
        mock_db_session.merge.assert_called_once()
        mock_db_session.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main() 