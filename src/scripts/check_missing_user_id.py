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

print("🔍 Scanning DynamoDB for entries missing 'user_id'...")

response = table.scan()
items = response.get("Items", [])
missing = []

for item in items:
    if "user_id" not in item:
        missing.append(item)

print(f"✅ Total items scanned: {len(items)}")
print(f"❌ Entries missing 'user_id': {len(missing)}")

for i, entry in enumerate(missing, 1):
    print(f"\n[{i}] {entry}")
