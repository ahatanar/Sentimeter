from flask import Blueprint, redirect, request, jsonify, url_for
from flask_jwt_extended import create_access_token
from oauthlib.oauth2 import WebApplicationClient
from src.models.user_model import UserModel
from src.utils.database import get_table
import requests
import os

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Login with Google
@auth_bp.route("/login", methods=["GET"])
def login():
    # Get Google's authorization endpoint
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Create the Google OAuth login URL
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=url_for("auth.callback", _external=True),
        scope=["openid", "email", "profile"]
    )
    return redirect(request_uri)

# Callback Endpoint
@auth_bp.route("/callback", methods=["GET"])
def callback():
    # Get the authorization code from Google
    code = request.args.get("code")

    # Get Google's token endpoint
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Exchange the authorization code for tokens
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=url_for("auth.callback", _external=True),
        client_secret=GOOGLE_CLIENT_SECRET
    )
    token_response = requests.post(token_url, headers=headers, data=body)
    client.parse_request_body_response(token_response.text)

    # Get user info from Google's userinfo endpoint
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # Extract user information
    user_info = userinfo_response.json()
    google_id = user_info["sub"]
    email = user_info["email"]
    name = user_info.get("name", "User")

    # Check if user exists in the database
    user = UserModel.find_by_google_id(google_id)
    if not user:
        # Create a new user if not found
        UserModel.save(google_id, email, name)

    # Create a JWT
    token = create_access_token(identity={"google_id": google_id, "email": email, "name": name})

    return jsonify({"token": token, "message": "Login successful!"}), 200