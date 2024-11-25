from transformers import pipeline

# Load the sentiment analysis pipeline
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

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