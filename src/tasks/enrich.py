import os
from celery import Celery
from datetime import datetime
from src.app import create_app
from src.database import db
from src.models.journal_model import JournalEntryModel
from src.services.text_service import TextAnalysisService
from src.services.weather_service import WeatherService

from src.celery_app import celery_app as celery

@celery.task(bind=True, acks_late=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def enrich_journal_entry(self, entry_id):
    import gc
    print(f"[TASK START] Processing entry {entry_id}", flush=True)
    app = create_app()
    
    try:
        with app.app_context():
            print(f"[TASK] Database lookup for entry {entry_id}", flush=True)
            entry = db.session.query(JournalEntryModel).get(entry_id)
            if not entry or not entry.processing:
                return  

            coords = None
            if entry.location and isinstance(entry.location, dict) and entry.location.get('latitude') and entry.location.get('longitude'):
                coords = (entry.location['latitude'], entry.location['longitude'])
            if coords:
                location = WeatherService.reverse_geocode(*coords)
            elif entry.ip_address:
                location = WeatherService.get_location_from_ip(entry.ip_address)
            else:
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
            
    except Exception as e:
        print(f"Error enriching entry {entry_id}: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Clean up memory after each task
        from src.services.text_service import cleanup_models
        cleanup_models()
        gc.collect() 