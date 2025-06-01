# scripts/embed_existing_entries_openai.py

import os
import time
import openai
from decimal import Decimal
from dotenv import load_dotenv

from database import get_table

# Load environment variables and setup OpenAI
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
        print(f"❌ Failed to embed: {e}")
        return None

def embed_existing_entries():
    response = table.scan()
    items = response.get("Items", [])

    print(f"Embedding {len(items)} journal entries using OpenAI...")

    for item in items:
        entry_id = item.get("entry_id")
        user_id = item.get("user_id")
        timestamp = item.get("timestamp")
        text = item.get("entry", "")

        if not all([entry_id, user_id, timestamp, text]):
            continue

        if "embedding" in item:
            print(f"Skipping already-embedded: {entry_id}")
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
                print(f"Embedded: {entry_id}")
                time.sleep(0.2)  

            except Exception as e:
                print(f"Failed to save embedding for {entry_id}: {e}")

    print("🎉 Done embedding all entries with OpenAI.")

if __name__ == "__main__":
    embed_existing_entries()
