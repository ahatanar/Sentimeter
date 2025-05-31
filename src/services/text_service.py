from transformers import pipeline
import requests
import os
import openai
from keybert import KeyBERT
from random import Random
from openai import OpenAI
client = OpenAI()
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
HUGGING_FACE = os.getenv("HUGGING_FACE")
kw_model = KeyBERT('sentence-transformers/all-MiniLM-L6-v2')

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
        results = sentiment_pipeline(text, truncation=True)
        sentiment = results[0]["label"].lower() 
        confidence = results[0]["score"]

       
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

        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 1),  
            stop_words='english',        
            top_n=top_n                  
        )
        print(keywords)
        return [kw[0] for kw in keywords]  
        

    def generate_weather_description(weather_data):
        """
        Generate a descriptive weather summary using OpenAI's GPT-3.5-turbo model.
        
        :param weather_data: Dictionary containing weather details (e.g., temperature, humidity, description).
        :return: AI-generated weather description as a string.
        """
    
        prompt = (
        f"The weather details are as follows:\n"
        f"- Temperature: {weather_data.get('temperature', 'N/A')}°C\n"
        f"- Humidity: {weather_data.get('humidity', 'N/A')}%\n"
        f"- Condition: {weather_data.get('description', 'N/A')}\n"
        f"- Wind Speed: {weather_data.get('wind_speed', 'N/A')} m/s\n\n"
        f"Now, write a short, accurate weather description for a journal entry. Be descriptive and factual like combine casual casual conversation tone with scientific tone to be accurate, for example sunny with x degrees dark windy day with 45kmh winds. give thetext description, or be like fast winds, humid etc, limit response to 150 chars at maximum "
        )

        try:
            response = client.chat.completions.create(
            model="gpt-4o-2024-08-06", 
            messages=[
                {
                    "role": "system",
                    "content": "You are a weather describing robot",
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ],
            max_tokens=150,
            temperature=0.5,  
        )

            weather_description = response.choices[0].message.content.strip()
            return weather_description
        except Exception as e:
            print(f"[ERROR] OpenAI API call failed: {e}")
            return "Description not available."