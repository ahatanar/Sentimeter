#!/usr/bin/env python3
"""
Test script for the refactored TextAnalysisService
"""

from src.services.text_service import TextAnalysisService

def test_text_analysis_service():
    """Test the refactored TextAnalysisService"""
    
    print("🧪 Testing Refactored TextAnalysisService")
    print("=" * 50)
    
    # Test 1: Default configuration (HuggingFace + OpenAI)
    print("\n1️⃣ Testing Default Configuration:")
    service = TextAnalysisService()
    
    test_text = "I had a wonderful day today! The weather was perfect and I felt great."
    
    # Test sentiment analysis
    sentiment, confidence = service.analyze_sentiment(test_text)
    print(f"   Sentiment: {sentiment} (confidence: {confidence:.3f})")
    
    # Test keyword extraction
    keywords = service.extract_keywords(test_text, top_n=3)
    print(f"   Keywords: {keywords}")
    
    # Test weather description
    weather_data = {
        'temperature': 22,
        'humidity': 65,
        'description': 'partly cloudy',
        'wind_speed': 12
    }
    weather_desc = service.generate_weather_description(weather_data)
    print(f"   Weather: {weather_desc}")
    
    # Test 2: Switch to OpenAI for sentiment
    print("\n2️⃣ Testing OpenAI Sentiment Analysis:")
    service.switch_sentiment_provider("openai")
    sentiment, confidence = service.analyze_sentiment(test_text)
    print(f"   Sentiment: {sentiment} (confidence: {confidence:.3f})")
    
    # Test 3: Switch to OpenAI for keywords
    print("\n3️⃣ Testing OpenAI Keyword Extraction:")
    service.switch_keyword_provider("openai")
    keywords = service.extract_keywords(test_text, top_n=3)
    print(f"   Keywords: {keywords}")
    
    # Test 4: Switch back to HuggingFace
    print("\n4️⃣ Switching Back to HuggingFace:")
    service.switch_sentiment_provider("huggingface")
    service.switch_keyword_provider("huggingface")
    
    sentiment, confidence = service.analyze_sentiment(test_text)
    print(f"   Sentiment: {sentiment} (confidence: {confidence:.3f})")
    
    keywords = service.extract_keywords(test_text, top_n=3)
    print(f"   Keywords: {keywords}")
    
    print("\n✅ All tests completed successfully!")
    print("\n🎯 Benefits of this refactoring:")
    print("   • Easy to swap providers at runtime")
    print("   • Clean separation of concerns")
    print("   • Easy to add new providers")
    print("   • Type-safe interfaces")
    print("   • Factory pattern for instantiation")

if __name__ == "__main__":
    test_text_analysis_service() 