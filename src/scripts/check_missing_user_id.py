# scripts/check_missing_user_id.py

import os
import boto3
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource(
    "dynamodb",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

table = dynamodb.Table("journals")

response = table.scan()
items = response.get("Items", [])
missing = []

for item in items:
    if "user_id" not in item:
        missing.append(item)
