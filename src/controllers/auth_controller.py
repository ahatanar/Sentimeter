from flask import Blueprint, redirect, request, jsonify, url_for,  make_response
from flask_jwt_extended import create_access_token,set_access_cookies
from oauthlib.oauth2 import WebApplicationClient
from src.models.user_model import UserModel
from src.database import get_table
import requests
import os
from flask_jwt_extended import get_jwt_identity, jwt_required
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

client = WebApplicationClient(GOOGLE_CLIENT_ID)


def extract_user_id():
    """
    Extract the `google_id` from the JWT payload.
    
    :return: The `google_id` of the authenticated user.
    """
    return get_jwt_identity()["google_id"]
@auth_bp.route("/login", methods=["GET"])
def login():

    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
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

        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
      
        user_info = userinfo_response.json()
        google_id = user_info["sub"]
        email = user_info["email"]
        name = user_info.get("name", "User")
        print(f"Google ID: {google_id}, Email: {email}, Name: {name}")

        user = UserModel.find_by_google_id(google_id)
        if not user:
            print("User not found in the database. Creating a new user.")
            UserModel.save(google_id, email, name)
        else:
            print("User found in the database.")

        token = create_access_token(identity={"google_id": google_id, "email": email, "name": name})
        print("are we not redirecting222?")
        response = make_response(redirect("http://localhost:3000/"))

        response.set_cookie(
        "access_token_cookie",
        token,
        samesite="None",   
        secure=True,          
    )
        return response
        return jsonify({"token": token, "message": "Login successful!"}), 200

    except Exception as e:
        print(f"Error during callback: {e}")
        return jsonify({"error": "Failed to process callback"}), 500
    


@auth_bp.route("/user-info", methods=["GET"])
@jwt_required()  
def user_info():
# Log request headers
    print("Request headers:", dict(request.headers))

    # Log request cookies
    print("Request cookies:", request.cookies)

    try:
        user_id = extract_user_id()

        user = UserModel.find_by_google_id(user_id)

        return jsonify({
            "email": user.get("email"),
            "name": user.get("name"),
        }), 200
    except Exception as e:
        print(f"Error fetching user info: {e}")
        return jsonify({"error": "Failed to fetch user info"}), 500
    
@auth_bp.route("/authorize-calendar", methods=["GET"])
def authorize_calendar():
    try:
        # Discover Google's authorization endpoint
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Redirect the user to Google's OAuth screen for calendar access
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=url_for("auth.calendar_callback", _external=True),
            scope=["https://www.googleapis.com/auth/calendar.events"],
            access_type="offline"  # Offline access to get a refresh token
        )
        return redirect(request_uri)
    except Exception as e:
        return jsonify({"error": f"Failed to initiate calendar authorization: {e}"}), 500

@auth_bp.route("/calendar-callback", methods=["GET"])
def calendar_callback():
    try:
        code = request.args.get("code")

        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=url_for("auth.calendar_callback", _external=True),
            client_secret=GOOGLE_CLIENT_SECRET,
        )
        token_response = requests.post(token_url, headers=headers, data=body)
        token_response_data = client.parse_request_body_response(token_response.text)

        access_token = token_response_data["access_token"]

        jwt_token = create_access_token(identity={"access_token": access_token})
        return jsonify({"jwt_token": jwt_token, "message": "Calendar access authorized!"}), 200
    except Exception as e:
        return jsonify({"error": f"Could not get authorization: {e}"}), 500
    


@auth_bp.route("/addevent", methods=["POST"])
@jwt_required()  
def add_event():
    try:
        print("Reached endpoint")  

        user_identity = get_jwt_identity()
        access_token = user_identity.get("access_token")
        if not access_token:
            return jsonify({"error": "No Authorization"}), 401
        event_details = request.json
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers=headers,
            json=event_details,
        )

        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": f"Failed to add event: {e}"}), 500