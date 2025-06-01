import os
from dotenv import load_dotenv
from database import get_table
from datetime import datetime

load_dotenv()

def is_valid_iso_timestamp(ts):
    try:
        datetime.fromisoformat(ts)
        return True
    except Exception:
        return False

def check_invalid_timestamps():
    table = get_table("journals")
    print("🔍 Scanning for entries with invalid or missing timestamps...")
    
    response = table.scan()
    items = response.get("Items", [])
    
    bad_items = []
    for item in items:
        ts = item.get("timestamp")
        if not ts or not isinstance(ts, str) or not is_valid_iso_timestamp(ts):
            bad_items.append(item)

    print(f"✅ Total items scanned: {len(items)}")
    print(f"❌ Entries with invalid/missing timestamps: {len(bad_items)}")

    for bad in bad_items:
        print(f"- entry_id: {bad.get('entry_id')} | timestamp: {bad.get('timestamp')}")

if __name__ == "__main__":
    check_invalid_timestamps()