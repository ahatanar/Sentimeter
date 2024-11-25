import sys
import os
import boto3
from flask import Flask
from src.config import Config
from src.controllers.jorunal_controller import quiz_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize DynamoDB
    try:
        dynamodb = boto3.resource(
            "dynamodb",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        app.dynamodb = dynamodb  # Add DynamoDB to Flask app context
        print("DynamoDB connected successfully.")
    except Exception as e:
        print("Error connecting to DynamoDB:", e)
        sys.exit(1)  # Exit if unable to connect to DynamoDB

    # Register blueprints
    app.register_blueprint(quiz_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)