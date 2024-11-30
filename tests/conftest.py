import pytest
from unittest.mock import patch, MagicMock
from src.app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "AWS_ACCESS_KEY_ID": "test",  # Dummy keys
            "AWS_SECRET_ACCESS_KEY": "test",
            "AWS_REGION": "us-east-1",
        }
    )
    yield app


@pytest.fixture
def dynamodb_mock():
    # Mock boto3 resource and DynamoDB tables
    with patch("boto3.resource") as mock_boto3:
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()

        # Configure mock table responses
        mock_table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        mock_table.get_item.return_value = {
            "Item": {"user_id": "user1", "timestamp": 1234567890, "entry": "Mock entry"}
        }
        mock_table.query.return_value = {
            "Items": [
                {"user_id": "user1", "timestamp": 1234567890, "entry": "Mock entry"}
            ]
        }

        # Assign mock table to specific DynamoDB tables
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3.return_value = mock_dynamodb

        yield mock_dynamodb