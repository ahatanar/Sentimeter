import os
from datetime import datetime
import sys
from datetime import timedelta
import boto3
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from src.controllers.auth_controller import auth_bp
from src.controllers.jorunal_controller import journal_bp
# Initialize SQLAlchemy
# db = SQLAlchemy()

# Define the table model
# class Entry(db.Model):
#     __tablename__ = 'entries'

#     id = db.Column(db.String(100), primary_key=True, nullable=False)
#     title = db.Column(db.String(255), nullable=False)
#     content = db.Column(db.Text, nullable=False)
#     date = db.Column(db.String(50), nullable=False)
#     sentiment = db.Column(db.String(50), nullable=False)

#     def __repr__(self):
#         return f'<Entry {self.title}>'

#     # Method to return a formatted date
#     def formatted_date(self):
#         # Parse ISO 8601 date and format it as YYYY-MM-DD
#         return datetime.strptime(self.date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")

def create_app():
    app = Flask(__name__)

    # Configure MySQL database
    # app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:kevinwaran123@localhost/kevin"
    # app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # app.config["CORS_HEADERS"] = "Content-Type"
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "default_jwt_secret")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

    # Initialize extensions
    JWTManager(app)
    CORS(app)

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

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(journal_bp)
    return app

if __name__ == "__main__":
    app = create_app()

  

    app.run(debug=True)
