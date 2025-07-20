import os
import requests

BACKEND_URL = "http://127.0.0.1:5000"  # Change if needed
API_URL = f"{BACKEND_URL}/api/journals"

# Read JWT token from environment variable
jwt_token = os.getenv("JOURNAL_TEST_JWT")
if not jwt_token:
    print("Set JOURNAL_TEST_JWT environment variable with your JWT token.")
    exit(1)

cookies = {
    "access_token_cookie": jwt_token
}

payload = {
    "entry": "This is a test journal entry from backend.",
    # "date": "2024-07-20T14:30:00",  # Optional, ISO format
    # "location": {"latitude": 40.7128, "longitude": -74.0060}  # Optional
}

response = requests.post(API_URL, json=payload, cookies=cookies)

print("Status code:", response.status_code)
try:
    print("Response:", response.json())
except Exception:
    print("Response (non-JSON):", response.text) 