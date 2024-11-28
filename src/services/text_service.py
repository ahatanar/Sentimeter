from transformers import pipeline
import requests
import os
import openai
from keybert import KeyBERT
from random import random
from openai import OpenAI
client = OpenAI()
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
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
        if sentiment=="negative":
            confidence = -1*confidence

        if -0.5 <= confidence <= 0.5:
            sentiment = "neutral"
        return sentiment, confidence

    @staticmethod
    def extract_keywords(text, top_n = 5):
        """
        Extract keywords from the given text using a pre-trained ML model.
        :param text: The input text to extract keywords from.
        :param max_keywords: The maximum number of keywords to extract.
        :return: List of extracted keywords.
        """
        kw_model = KeyBERT('sentence-transformers/all-MiniLM-L6-v2')

        print("loaded model")
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 1),  # Single words and bigrams
            stop_words='english',         # Remove common stop words
            top_n=top_n                   # Number of keywords to extract
        )
        print("didnt return")
        print(keywords)
        return [kw[0] for kw in keywords]  # Return keywords only
        



    openai.api_key = "your_openai_api_key"

    def generate_weather_description(weather_data):
        """
        Generate a descriptive weather summary using OpenAI's GPT-3.5-turbo model.
        
        :param weather_data: Dictionary containing weather details (e.g., temperature, humidity, description).
        :return: AI-generated weather description as a string.
        """
        # Assign a random city if the city is unknown
        if weather_data.get('city', 'unknown') == "unknown":
            weather_data['city'] = random.choice(
                ["New York", "Beijing", "Oshawa", "Toronto", "Vatican City", 
                "London", "Birmingham", "Miami", "Palo Alto", "Sacramento", 
                "Austin", "Houston", "Seattle"]
            )

        # Define the prompt
        prompt = (
            f"The weather details are as follows:\n"
            f"- City: {weather_data.get('city', 'N/A')}\n"
            f"- Temperature: {weather_data.get('temperature', 'N/A')}°C\n"
            f"- Humidity: {weather_data.get('humidity', 'N/A')}%\n"
            f"- Condition: {weather_data.get('description', 'N/A')}\n"
            f"- Wind Speed: {weather_data.get('wind_speed', 'N/A')} m/s\n\n"
            f"Now, write a short, vivid weather description for a journal entry. Be descriptive and engaging."
        )

        try:
            # Correct API call
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a creative assistant generating weather descriptions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7,
            )
            # Extract the response correctly
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[ERROR] OpenAI API call failed: {e}")
            return "Description not available."