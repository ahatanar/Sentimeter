import os
from datetime import datetime
import sys
from datetime import timedelta
import boto3
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
# from controllers.auth_controller import auth_bp

# Initialize SQLAlchemy
db = SQLAlchemy()

# Define the table model
class Entry(db.Model):
    __tablename__ = 'entries'

    id = db.Column(db.String(100), primary_key=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    sentiment = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<Entry {self.title}>'

    # Method to return a formatted date
    def formatted_date(self):
        # Parse ISO 8601 date and format it as YYYY-MM-DD
        return datetime.strptime(self.date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")

def create_app():
    app = Flask(__name__)

    # Configure MySQL database
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:kevinwaran123@localhost/kevin"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["CORS_HEADERS"] = "Content-Type"
    # app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")
    # app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "default_jwt_secret")
    # app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

    # Initialize extensions
    db.init_app(app)
    JWTManager(app)
    CORS(app)

    # Optional: Connect to DynamoDB (if used elsewhere in the app)
    # try:
    #     dynamodb = boto3.resource(
    #         "dynamodb",
    #         aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    #         aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    #         region_name=os.getenv("AWS_REGION"),
    #     )
    #     app.dynamodb = dynamodb  
    #     print("DynamoDB connected successfully.")
    # except Exception as e:
    #     print("Error connecting to DynamoDB:", e)
    #     sys.exit(1)

    # # Register blueprints
    # app.register_blueprint(auth_bp)

    @app.route("/store_data", methods=["POST"])
    def store_data():
        data = request.get_json()

        if data:
            try:
                id_ = data.get("id")
                title = data.get("title")
                content = data.get("content")
                date = data.get("date")
                sentiment = data.get("sentiment")

                new_entry = Entry(
                    id=id_,
                    title=title,
                    content=content,
                    date=date,
                    sentiment=sentiment
                )
                db.session.add(new_entry)
                db.session.commit()

                return jsonify({"message": "Data inserted successfully", "status": "success"}), 200
            except Exception as e:
                return jsonify({"message": "Failed to insert data", "error": str(e), "status": "error"}), 500
        else:
            return jsonify({"message": "Invalid or missing JSON data", "status": "error"}), 400
        
    @app.route('/delete_entry/<int:entry_id>', methods=['DELETE'])
    def delete_entry(entry_id):
        try:
            entry = Entry.query.get({"id":entry_id})
            if entry:
                db.session.delete(entry)
                db.session.commit()
                return jsonify({"message": f"Entry with ID {entry_id} deleted successfully", "status": "success"}), 200
            else:
                return jsonify({"message": f"Entry with ID {entry_id} not found", "status": "error"}), 404
        except Exception as e:
            return jsonify({"message": "Error occurred while deleting entry", "error": str(e), "status": "error"}), 500
        
    @app.route('/get_entries', methods=['GET'])
    def get_entries():
        entries = Entry.query.all()
        serialized = [{"id": entry.id, "title": entry.title, "content": entry.content,
                    "date": entry.date, "sentiment": entry.sentiment} for entry in entries]
        return jsonify({"entries": serialized}), 200
    
    @app.route('/api/journal', methods=['GET'])
    def get_journal_entries():
        entries = Entry.query.all()
        entries_list = [{
            'id': entry.id,
            'title': entry.title,
            'content': entry.content,
            'date': entry.formatted_date(),  # Format the date for frontend
            'sentiment': entry.sentiment
        } for entry in entries]
        return jsonify(entries_list)


    return app

if __name__ == "__main__":
    app = create_app()

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    app.run(debug=True)
