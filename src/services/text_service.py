from transformers import pipeline
import requests
import os
# Initialize pipelines globally for efficiency
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
keyword_pipeline = pipeline("feature-extraction", model="sentence-transformers/all-MiniLM-L6-v2")  # Pre-trained model for keywords
HUGGING_FACE = os.getenv("HUGGING_FACE")

class TextAnalysisService:
    """
    A service for performing text analysis, including sentiment analysis and keyword extraction.
    """

    @staticmethod
    def analyze_sentiment(text):
        """
        Analyze the sentiment of a given text (positive, neutral, or negative).
        :param text: The input text to analyze.
        :return: Sentiment (positive/neutral/negative) and confidence score.
        """
        # Get sentiment prediction
        results = sentiment_pipeline(text, truncation=True)
        sentiment = results[0]["label"].lower()  # Convert to lowercase for uniformity
        confidence = results[0]["score"]

        # Normalize the sentiment to include 'neutral' if applicable
        if sentiment == "positive" and confidence < 0.6:  # Low confidence positive is neutral
            sentiment = "neutral"
        elif sentiment == "negative" and confidence < 0.6:  # Low confidence negative is neutral
            sentiment = "neutral"

        return sentiment, confidence

    @staticmethod
    def extract_keywords(text, max_keywords=5):
        """
        Extract keywords from the given text using a pre-trained ML model.
        :param text: The input text to extract keywords from.
        :param max_keywords: The maximum number of keywords to extract.
        :return: List of extracted keywords.
        """
        # Use the keyword pipeline to generate embeddings
        embeddings = keyword_pipeline(text)

        # For simplicity, treat the embeddings' largest-weighted words as "keywords"
        # Advanced: Fine-tune this logic for real keyword ranking.
        words = text.split()  # Split text into words (tokenization can be improved)
        word_weights = [sum(embedding) for embedding in embeddings[0]]

        # Pair words with weights, sort by weight, and extract the top keywords
        word_weights = list(zip(words, word_weights))
        sorted_keywords = sorted(word_weights, key=lambda x: x[1], reverse=True)
        keywords = [word for word, _ in sorted_keywords[:max_keywords]]

        return keywords
    
    import requests

    def generate_weather_description(weather_data):
        """
        Generate a descriptive weather summary using Hugging Face's GPT-2 model.
        
        :param weather_data: Dictionary containing weather details (e.g., temperature, humidity, description).
        :return: AI-generated weather description as a string.
        """
        api_url = "https://api-inference.huggingface.co/models/gpt2"
        headers = {"Authorization": f"{HUGGING_FACE}"} 

        prompt = (
            f"Provide a descriptive summary of the weather based on the following details:\n"
            f"- Temperature: {weather_data['temperature']}°C\n"
            f"- Humidity: {weather_data['humidity']}%\n"
            f"- Condition: {weather_data['description']}\n"
            f"- Wind Speed: {weather_data.get('wind_speed', 'N/A')} m/s\n\n"
            f"Write a short and engaging paragraph about the current weather conditions."
        )

        payload = {"inputs": prompt}

        try:
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()  

            result = response.json()

            return result[0]["generated_text"] if isinstance(result, list) else "Description not available."
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Hugging Face API call failed: {e}")
            return "Description not available."