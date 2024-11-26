from flask import Blueprint, redirect, request, jsonify, url_for
from flask_jwt_extended import create_access_token
from oauthlib.oauth2 import WebApplicationClient
from src.models.user_model import UserModel
from src.database import get_table
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
    print("Login endpoint hit")

    try:
        print("try")
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        print("check after geetting discovery",google_provider_cfg)
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        print(f"Authorization endpoint: {authorization_endpoint}")

        # Create the Google OAuth login URL
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=url_for("auth.callback", _external=True),
            scope=["openid", "email", "profile"]
        )
        print(f"Request URI: {request_uri}")
        return redirect(request_uri)
    except Exception as e:
        print(f"Error during login: {e}")
        return jsonify({"error": "Failed to initiate login"}), 500

# Callback Endpoint
@auth_bp.route("/callback", methods=["GET"])
def callback():
    try:
        # Get the authorization code from Google
        code = request.args.get("code")
        print(f"Authorization code: {code}")

        # Get Google's token endpoint
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        print(f"Token endpoint: {token_endpoint}")

        # Exchange the authorization code for tokens
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=url_for("auth.callback", _external=True),
            client_secret=GOOGLE_CLIENT_SECRET
        )
        print(f"Token request body: {body}")
        token_response = requests.post(token_url, headers=headers, data=body)
        print(f"Token response status: {token_response.status_code}")
        print(f"Token response body: {token_response.text}")

        client.parse_request_body_response(token_response.text)

        # Get user info from Google's userinfo endpoint
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        print(f"User info response: {userinfo_response.status_code}")
        print(f"User info body: {userinfo_response.text}")

        # Extract user information
        user_info = userinfo_response.json()
        google_id = user_info["sub"]
        email = user_info["email"]
        name = user_info.get("name", "User")
        print(f"Google ID: {google_id}, Email: {email}, Name: {name}")

        # Check or create user in the database
        user = UserModel.find_by_google_id(google_id)
        if not user:
            print("User not found in the database. Creating a new user.")
            UserModel.save(google_id, email, name)
        else:
            print("User found in the database.")

        # Create a JWT
        token = create_access_token(identity={"google_id": google_id, "email": email, "name": name})
        print(f"JWT Token: {token}")

        return jsonify({"token": token, "message": "Login successful!"}), 200

    except Exception as e:
        print(f"Error during callback: {e}")
        return jsonify({"error": "Failed to process callback"}), 500