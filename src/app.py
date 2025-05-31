import os
from dotenv import load_dotenv

load_dotenv()
from datetime import datetime
import sys
from datetime import timedelta
import boto3
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from controllers.auth_controller import auth_bp
from controllers.journal_controller import journal_bp





def create_app():
    app = Flask(__name__)


    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "default_jwt_secret")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]   
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False  
    app.config["JWT_COOKIE_SAMESITE"] = "None"  
    app.config["JWT_COOKIE_SECURE"] = False  
    CORS(app, supports_credentials=True, origins=["http://localhost:3000","https://sentimeter-frontend.vercel.app"])


    jwt = JWTManager(app)
    try:
        dynamodb = boto3.resource(
            "dynamodb",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        app.dynamodb = dynamodb  
        print("DynamoDB connected successfully.")
    except Exception as e:
        print("Error connecting to DynamoDB:", e)
        sys.exit(1)

    app.register_blueprint(auth_bp)
    app.register_blueprint(journal_bp)
    return app

if __name__ == "__main__":
    print("APP STARTING", flush=True)
    app = create_app()
    app.run(debug=True, use_reloader=False)


