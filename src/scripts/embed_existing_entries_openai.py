# scripts/embed_existing_entries_openai.py

import os
import time
import openai
from decimal import Decimal
from dotenv import load_dotenv

from src.database import get_table

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
table = get_table("journals")

def get_openai_embedding(text):
    try:
        response = openai.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        return None

def embed_existing_entries():
    total_embedded = 0
    last_evaluated_key = None

    while True:
        scan_kwargs = {}
        if last_evaluated_key:
            scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

        response = table.scan(**scan_kwargs)
        items = response.get("Items", [])

        for item in items:
            entry_id = item.get("entry_id")
            user_id = item.get("user_id")
            timestamp = item.get("timestamp")
            text = item.get("entry", "")

            if not all([entry_id, user_id, timestamp, text]):
                continue

            if "embedding" in item:
                continue

            embedding = get_openai_embedding(text)
            if embedding:
                try:
                    embedding_decimal = [Decimal(str(x)) for x in embedding]
                    table.update_item(
                        Key={"user_id": user_id, "timestamp": timestamp},
                        UpdateExpression="SET embedding = :vec",
                        ExpressionAttributeValues={":vec": embedding_decimal}
                    )
                    total_embedded += 1
                    time.sleep(0.2)
                except Exception as e:
                    pass

        if "LastEvaluatedKey" not in response:
            break
        last_evaluated_key = response["LastEvaluatedKey"]


if __name__ == "__main__":
    embed_existing_entries()
