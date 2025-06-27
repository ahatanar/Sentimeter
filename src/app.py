import os
from dotenv import load_dotenv

load_dotenv()
from datetime import datetime
import sys
from datetime import timedelta
import boto3
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from src.controllers.auth_controller import auth_bp
from src.controllers.journal_controller import journal_bp
from src.database import db

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "default_jwt_secret")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]   
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False  
    app.config["JWT_COOKIE_SAMESITE"] = "None"  
    app.config["JWT_COOKIE_SECURE"] = False  
    CORS(app, supports_credentials=True, origins=["http://localhost:3000","https://sentimeter-frontend.vercel.app"])

    db.init_app(app)

    jwt = JWTManager(app)


    app.register_blueprint(auth_bp)
    app.register_blueprint(journal_bp)
    return app

if __name__ == "__main__":
    print("APP STARTING", flush=True)
    app = create_app()
    app.run(debug=True, use_reloader=False)


