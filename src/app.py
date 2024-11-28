import sys
import os
import boto3
from flask import Flask
from src.config import Config
from src.controllers.jorunal_controller import journal_bp  # Correct import
from src.services.journal_service import JournalService
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from src.controllers.auth_controller import auth_bp
from datetime import timedelta


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)  # 24 hours for access tokens

    jwt = JWTManager(app)
    CORS(app, supports_credentials=True)
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
    app = create_app()
    app.run(debug=True)
