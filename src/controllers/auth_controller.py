from flask import Blueprint, request, redirect, jsonify, make_response, url_for
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.models.user_model import User


import requests
import os
from flask_jwt_extended import jwt_required

from oauthlib.oauth2 import WebApplicationClient

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
FRONTEND_REDIRECT_URI = os.getenv("FRONTEND_REDIRECT_URI")

client = WebApplicationClient(GOOGLE_CLIENT_ID)
REDIRECT_URI = os.getenv("REDIRECT_URI")

@auth_bp.route("/login", methods=["GET"])
def login():
    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=REDIRECT_URI,
            scope=["openid", "email", "profile"]
        )

        return redirect(request_uri)

    except Exception as e:
        return jsonify({"error": "Failed to initiate login"}), 500


@auth_bp.route("/callback", methods=["GET"])
def callback():
    print("=== AUTH CALLBACK START ===", flush=True)
    print(f"Request URL: {request.url}", flush=True)
    print(f"Request args: {request.args}", flush=True)
    print(f"FRONTEND_REDIRECT_URI: {FRONTEND_REDIRECT_URI}", flush=True)
    print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT')}", flush=True)
    
    try:
        print("Callback URL hit:", request.url, flush=True)

        code = request.args.get("code")
        if not code:
            return jsonify({"error": "Missing code parameter"}), 400


        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]

        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=REDIRECT_URI,
            client_secret=GOOGLE_CLIENT_SECRET
        )

        token_response = requests.post(token_url, headers=headers, data=body)

        if not token_response.ok:
            return jsonify({"error": "Failed to get token from Google"}), 500

        client.parse_request_body_response(token_response.text)

        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        if not userinfo_response.ok:
            return jsonify({"error": "Failed to get user info"}), 500

        user_info = userinfo_response.json()
        google_id = user_info["sub"]
        email = user_info["email"]
        name = user_info.get("name", "User")

        user = User.find_by_google_id(google_id)
        if not user:
            User.save(google_id, email, name)


        token = create_access_token(identity=google_id)
        print(f"Created JWT token for user: {google_id}", flush=True)
        print(f"Token length: {len(token)}", flush=True)
        
        # Return HTML with cookie setting and redirect
        html_response = f"""
        <html>
        <body>
        <script>
        document.cookie = "access_token_cookie={token}; path=/; max-age=86400; samesite=None; secure";
        window.location.href = "{FRONTEND_REDIRECT_URI}";
        </script>
        <p>Redirecting...</p>
        </body>
        </html>
        """
        
        response = make_response(html_response, 200)
        response.headers['Content-Type'] = 'text/html'
        response.headers['Access-Control-Allow-Origin'] = 'https://sentimeter-frontend.vercel.app'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        print("=== AUTH CALLBACK SUCCESS ===", flush=True)
        return response

    except Exception as e:
        print(f"Callback error: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to process callback: {str(e)}"}), 500



@auth_bp.route("/user-info", methods=["GET"])
@jwt_required()
def user_info():
    """
    Retrieves authenticated user information.

    This endpoint fetches the user's email and name from the database based on
    their Google ID, which is extracted from the JWT token.

    Returns:
        - 200 OK: A JSON object containing the user's email and name.
        - 500 Error: A JSON object with an error message if fetching user info fails.
    """
    print("=== USER INFO REQUEST ===", flush=True)
    print(f"Request cookies: {request.cookies}", flush=True)
    
    try:
        identity = get_jwt_identity()
        print(f"JWT identity: {identity}", flush=True)
        user = User.find_by_google_id(identity)

        if not user:
            print(f"User not found for identity: {identity}", flush=True)
            return jsonify({"error": "User not found"}), 404

        print(f"User found: {user.email}", flush=True)
        return jsonify({
            "email": user.email,
            "name": user.name,
        }), 200
    except Exception as e:
        print(f"USER INFO ERROR: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to fetch user info: {str(e)}"}), 500
    
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
