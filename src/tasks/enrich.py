import os
from celery import Celery
from datetime import datetime
from src.app import create_app
from src.database import db
from src.models.journal_model import JournalEntryModel
from src.services.text_service import TextAnalysisService
from src.services.weather_service import WeatherService

celery = Celery(__name__, broker=os.getenv("REDIS_URL"))

@celery.task(bind=True, acks_late=True, autoretry_for=(Exception,), retry_backoff=True)
def enrich_journal_entry(self, entry_id):
    app = create_app()
    with app.app_context():
        entry = db.session.query(JournalEntryModel).get(entry_id)
        if not entry or not entry.processing:
            return  # Already enriched or doesn't exist

        # 1. Location
        coords = None
        if entry.location and isinstance(entry.location, dict) and entry.location.get('latitude') and entry.location.get('longitude'):
            coords = (entry.location['latitude'], entry.location['longitude'])
        if coords:
            print(f"[EnrichTask] Attempting reverse geocode for lat={coords[0]}, lon={coords[1]}")
            location = WeatherService.reverse_geocode(*coords)
            print(f"[EnrichTask] Reverse geocode result: {location}")
        elif entry.ip_address:
            print(f"[EnrichTask] Getting location from IP: {entry.ip_address}")
            location = WeatherService.get_location_from_ip(entry.ip_address)
            print(f"[EnrichTask] IP geocode result: {location}")
        else:
            print(f"[EnrichTask] No location or IP available, defaulting to unknown.")
            location = {"city": "Unknown", "region": "Unknown", "country": "Unknown"}

        # 2. Weather
        weather = WeatherService.get_weather_by_location(location)

        # 3. Text analysis
        service = TextAnalysisService()
        sentiment, sentiment_score = service.analyze_sentiment(entry.entry)
        keywords = service.extract_keywords(entry.entry)
        embedding = service.generate_embedding(entry.entry)

        # 4. Update entry
        entry.location = location
        entry.weather = weather
        entry.sentiment = sentiment
        entry.sentiment_score = sentiment_score
        entry.keywords = keywords
        entry.embedding = embedding
        entry.processing = False
        entry.last_enriched_at = datetime.utcnow()
        entry.ip_address = None  # Clear IP after use

        db.session.commit() 