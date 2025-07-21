from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# =========================================================================
# MODULE-LEVEL ML MODEL SINGLETONS (Loaded once per worker process)
# =========================================================================

# HuggingFace sentiment pipeline (CPU only)
_hf_sentiment_pipeline = None
# KeyBERT model
_hf_keybert_model = None

def get_hf_sentiment_pipeline():
    global _hf_sentiment_pipeline
    if _hf_sentiment_pipeline is None:
        from transformers import pipeline
        _hf_sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1  # Force CPU
        )
    return _hf_sentiment_pipeline

def get_hf_keybert_model():
    global _hf_keybert_model
    if _hf_keybert_model is None:
        from keybert import KeyBERT
        _hf_keybert_model = KeyBERT('sentence-transformers/all-MiniLM-L6-v2')
    return _hf_keybert_model

# Eagerly load models at worker startup
get_hf_sentiment_pipeline()
get_hf_keybert_model()

# =========================================================================
# ABSTRACT INTERFACES (Strategy Pattern)
# =========================================================================

class SentimentAnalyzer(ABC):
    """Strategy interface for sentiment analysis"""
    
    @abstractmethod
    def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """Analyze sentiment: returns (sentiment, confidence)"""
        pass

class KeywordExtractor(ABC):
    """Strategy interface for keyword extraction"""
    
    @abstractmethod
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """Extract keywords from text"""
        pass

class WeatherDescriber(ABC):
    @abstractmethod
    def generate_description(self, weather_data: Dict[str, Any]) -> str:
        pass

# =========================================================================
# CONCRETE IMPLEMENTATIONS
# =========================================================================

class HuggingFaceSentimentAnalyzer(SentimentAnalyzer):
    """Hugging Face implementation"""
    
    def __init__(self):
        # Use the module-level singleton
        self.pipeline = get_hf_sentiment_pipeline()
    
    def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        results = self.pipeline(text, truncation=True)
        sentiment = results[0]["label"].lower()
        confidence = results[0]["score"]
        
        if sentiment == "negative":
            confidence = -1 * confidence
        
        if -0.5 <= confidence <= 0.5:
            sentiment = "neutral"
        
        return sentiment, confidence

class OpenAISentimentAnalyzer(SentimentAnalyzer):
    """OpenAI implementation"""
    
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Analyze sentiment. Return 'positive', 'negative', or 'neutral' followed by confidence 0-1."},
                    {"role": "user", "content": f"Text: {text}"}
                ],
                max_tokens=10,
                temperature=0
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            if "positive" in result:
                confidence = float(result.split()[-1]) if len(result.split()) > 1 else 0.8
                return "positive", confidence
            elif "negative" in result:
                confidence = float(result.split()[-1]) if len(result.split()) > 1 else 0.8
                return "negative", -confidence
            else:
                return "neutral", 0.5
                
        except Exception as e:
            return "neutral", 0.0

class HuggingFaceKeywordExtractor(KeywordExtractor):
    """Hugging Face implementation"""
    
    def __init__(self):
        # Use the module-level singleton
        self.kw_model = get_hf_keybert_model()
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        keywords = self.kw_model.extract_keywords(
            text, keyphrase_ngram_range=(1, 1), stop_words='english', top_n=top_n
        )
        return [kw[0] for kw in keywords]

class OpenAIKeywordExtractor(KeywordExtractor):
    """OpenAI implementation"""
    
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Extract exactly {top_n} keywords. Return only keywords separated by commas."},
                    {"role": "user", "content": text}
                ],
                max_tokens=50,
                temperature=0
            )
            
            keywords = response.choices[0].message.content.strip()
            return [kw.strip() for kw in keywords.split(",")]
            
        except Exception as e:
            return []

class OpenAIWeatherDescriber(WeatherDescriber):
    def generate_description(self, weather_data: Dict[str, Any]) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        if weather_data.get('description', 'N/A') == 'unknown':
            return "Description not available."
        prompt = (
            f"Weather: {weather_data.get('temperature', 'N/A')}°C, "
            f"{weather_data.get('humidity', 'N/A')}% humidity, "
            f"{weather_data.get('description', 'N/A')}, "
            f"{weather_data.get('wind_speed', 'N/A')} m/s wind. "
            f"Write a short weather description (max 150 chars)."
        )
        try:
            response = client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "You are a weather describing robot"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return "Description not available."

class TemplateWeatherDescriber(WeatherDescriber):
    def generate_description(self, weather_data: Dict[str, Any]) -> str:
        return (
            f"{weather_data.get('description', 'N/A').capitalize()}, "
            f"{weather_data.get('temperature', 'N/A')}°C, "
            f"{weather_data.get('humidity', 'N/A')}% humidity, "
            f"{weather_data.get('wind_speed', 'N/A')} m/s wind."
        )

# =========================================================================
# MAIN SERVICE (Facade Pattern)
# =========================================================================

class TextAnalysisService:
    """
    Text analysis service with pluggable providers.
    Demonstrates Strategy Pattern for easy provider swapping.
    """
    
    def __init__(self, 
                 sentiment_provider: str = "huggingface",
                 keyword_provider: str = "huggingface",
                 weather_provider: str = "openai"):
        """
        Initialize with specified providers
        """
        self.sentiment_analyzer = self._create_sentiment_analyzer(sentiment_provider)
        self.keyword_extractor = self._create_keyword_extractor(keyword_provider)
        self.weather_describer = self._create_weather_describer(weather_provider)
    
    def _create_sentiment_analyzer(self, provider: str) -> SentimentAnalyzer:
        """Factory method for sentiment analyzers"""
        if provider == "huggingface":
            return HuggingFaceSentimentAnalyzer()
        elif provider == "openai":
            return OpenAISentimentAnalyzer()
        else:
            raise ValueError(f"Unsupported sentiment provider: {provider}")
    
    def _create_keyword_extractor(self, provider: str) -> KeywordExtractor:
        """Factory method for keyword extractors"""
        if provider == "huggingface":
            return HuggingFaceKeywordExtractor()
        elif provider == "openai":
            return OpenAIKeywordExtractor()
        else:
            raise ValueError(f"Unsupported keyword provider: {provider}")

    def _create_weather_describer(self, provider: str) -> WeatherDescriber:
        if provider == "openai":
            return OpenAIWeatherDescriber()
        elif provider == "template":
            return TemplateWeatherDescriber()
        else:
            raise ValueError(f"Unsupported weather provider: {provider}")
    
    def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """Analyze sentiment using current provider"""
        return self.sentiment_analyzer.analyze_sentiment(text)
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """Extract keywords using current provider"""
        return self.keyword_extractor.extract_keywords(text, top_n)

    def generate_weather_description(self, weather_data: Dict[str, Any]) -> str:
        return self.weather_describer.generate_description(weather_data)
    
    def switch_sentiment_provider(self, provider: str):
        """Switch sentiment analysis provider at runtime"""
        self.sentiment_analyzer = self._create_sentiment_analyzer(provider)
    
    def switch_keyword_provider(self, provider: str):
        """Switch keyword extraction provider at runtime"""
        self.keyword_extractor = self._create_keyword_extractor(provider)

    def switch_weather_provider(self, provider: str):
        """Switch weather description provider at runtime"""
        self.weather_describer = self._create_weather_describer(provider)

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        try:
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            return None