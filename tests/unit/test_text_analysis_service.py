import unittest
from unittest.mock import patch
from src.services.text_service import TextAnalysisService

class TestTextAnalysisService(unittest.TestCase):
    @patch("src.services.text_service.HuggingFaceSentimentAnalyzer.analyze_sentiment")
    def test_analyze_sentiment_positive(self, mock_analyze):
        mock_analyze.return_value = ("positive", 0.8)
        service = TextAnalysisService(sentiment_provider="huggingface")
        result = service.analyze_sentiment("This is great!")
        self.assertEqual(result, ("positive", 0.8))

    @patch("src.services.text_service.HuggingFaceSentimentAnalyzer.analyze_sentiment")
    def test_analyze_sentiment_neutral(self, mock_analyze):
        mock_analyze.return_value = ("neutral", 0.5)
        service = TextAnalysisService(sentiment_provider="huggingface")
        result = service.analyze_sentiment("It's okay.")
        self.assertEqual(result, ("neutral", 0.5))

    @patch("src.services.text_service.HuggingFaceSentimentAnalyzer.analyze_sentiment")
    def test_analyze_sentiment_negative(self, mock_analyze):
        mock_analyze.return_value = ("negative", -0.7)
        service = TextAnalysisService(sentiment_provider="huggingface")
        result = service.analyze_sentiment("This is bad!")
        self.assertEqual(result, ("negative", -0.7))

    @patch("src.services.text_service.HuggingFaceKeywordExtractor.extract_keywords")
    def test_extract_keywords(self, mock_extract_keywords):
        mock_extract_keywords.return_value = ["extraction", "keyword", "Test"]
        service = TextAnalysisService(keyword_provider="huggingface")
        result = service.extract_keywords("Test keyword extraction")
        self.assertEqual(result, ["extraction", "keyword", "Test"])
