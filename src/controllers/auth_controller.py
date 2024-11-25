from flask import Blueprint, redirect, url_for, session, jsonify,request
from flask_jwt_extended import create_access_token
from oauthlib.oauth2 import WebApplicationClient
import requests

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Google OAuth Configuration
GOOGLE_CLIENT_ID = "your-google-client-id"
GOOGLE_CLIENT_SECRET = "your-google-client-secret"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Login Endpoint: Redirect to Google
@auth_bp.route("/login", methods=["GET"])
def login():
    # Get Google's authorization URL
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Redirect user to Google's OAuth 2.0 server
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri="http://127.0.0.1:5000/api/auth/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

# Callback Endpoint: Handle Google's response
@auth_bp.route("/callback", methods=["GET"])
def callback():
    # Get authorization code from Google's response
    code = request.args.get("code")

    # Get Google's token endpoint
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url="http://127.0.0.1:5000/api/auth/callback",
        client_secret=GOOGLE_CLIENT_SECRET,
    )
    token_response = requests.post(token_url, headers=headers, data=body, auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET))

    # Parse tokens
    client.parse_request_body_response(token_response.text)

    # Get user info from Google's userinfo endpoint
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # Extract user info
    user_info = userinfo_response.json()
    google_id = user_info["sub"]
    email = user_info["email"]
    name = user_info.get("name", "User")

    # Generate JWT
    token = create_access_token(identity={"google_id": google_id, "email": email, "name": name})

    return jsonify({"token": token, "message": "Login successful!"}), 200