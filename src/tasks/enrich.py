import os
from celery import Celery
from datetime import datetime, timezone
from src.app import create_app
from src.database import db
from src.models.journal_model import JournalEntryModel
from src.services.text_service import TextAnalysisService
from src.services.weather_service import WeatherService

from src.celery_app import celery_app as celery

@celery.task(bind=True, acks_late=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3, soft_time_limit=300, time_limit=360)
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
            print("Getting GEODATA")
            if entry.location and isinstance(entry.location, dict) and entry.location.get('latitude') and entry.location.get('longitude'):
                coords = (entry.location['latitude'], entry.location['longitude'])
            if coords:
                location = WeatherService.reverse_geocode(*coords)
            elif entry.ip_address:
                location = WeatherService.get_location_from_ip(entry.ip_address)
            else:
                location = {"city": "Unknown", "region": "Unknown", "country": "Unknown"}

            # 2. Weather
            print("Getting Weather")
            weather = WeatherService.get_weather_by_location(location)

            # 3. Text analysis (memory optimized)
            print("Getting ML services", flush=True)
            
            # Use OpenAI for embedding to save memory
            from src.services.text_service import get_openai_client
            import gc
            
            # Only load HF models when needed
            service = TextAnalysisService()
            print("TextAnalysisService created", flush=True)
            
            print("Starting sentiment analysis...", flush=True)
            sentiment, sentiment_score = service.analyze_sentiment(entry.entry)
            print(f"Sentiment complete: {sentiment}", flush=True)
            
            print("Starting keyword extraction...", flush=True)
            keywords = service.extract_keywords(entry.entry)
            print(f"Keywords complete: {len(keywords)} found", flush=True)
            
            # Clean up HF models before OpenAI call
            from src.services.text_service import cleanup_models
            cleanup_models()
            gc.collect()
            
            print("Starting embedding generation...", flush=True)
            client = get_openai_client()
            try:
                response = client.embeddings.create(
                    input=entry.entry,
                    model="text-embedding-3-small"
                )
                embedding = response.data[0].embedding
            except Exception as e:
                print(f"Embedding failed: {e}")
                embedding = None
            print("Embedding complete", flush=True)

            # 4. Update entry
            entry.location = location
            entry.weather = weather
            entry.sentiment = sentiment
            entry.sentiment_score = sentiment_score
            entry.keywords = keywords
            entry.embedding = embedding
            entry.processing = False
            entry.last_enriched_at = datetime.now(timezone.utc)
            entry.ip_address = None  # Clear IP after use
            print("Succesfully enrichment now comitting to DB")
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