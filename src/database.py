import boto3
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize DynamoDB
def get_dynamodb_resource():
    return boto3.resource(
        "dynamodb",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
    )

# Get a specific DynamoDB table
def get_table(table_name):
    dynamodb = get_dynamodb_resource()
    return dynamodb.Table(table_name)
