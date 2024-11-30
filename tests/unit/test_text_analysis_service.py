import unittest
from unittest.mock import patch
from src.services.text_service import TextAnalysisService

class TestTextAnalysisService(unittest.TestCase):

    @patch("src.services.text_service.sentiment_pipeline")
    def test_analyze_sentiment_positive(self, mock_pipeline):
        mock_pipeline.return_value = [{"label": "POSITIVE", "score": 0.8}]
        result = TextAnalysisService.analyze_sentiment("This is great!")
        self.assertEqual(result, ("positive", 0.8))

    @patch("src.services.text_service.sentiment_pipeline")
    def test_analyze_sentiment_neutral(self, mock_pipeline):
        mock_pipeline.return_value = [{"label": "POSITIVE", "score": 0.5}]
        result = TextAnalysisService.analyze_sentiment("It's okay.")
        self.assertEqual(result, ("neutral", 0.5))

    @patch("src.services.text_service.sentiment_pipeline")
    def test_analyze_sentiment_negative(self, mock_pipeline):
        mock_pipeline.return_value = [{"label": "NEGATIVE", "score": 0.7}]
        result = TextAnalysisService.analyze_sentiment("This is bad!")
        self.assertEqual(result, ("negative", -0.7))

    @patch("src.services.text_service.kw_model.extract_keywords")
    def test_extract_keywords(self, mock_extract_keywords):
        mock_extract_keywords.return_value = [
            ("extraction", 0.9),
            ("keyword", 0.8),
            ("Test", 0.7)
        ]

        result = TextAnalysisService.extract_keywords("Test keyword extraction")

        self.assertEqual(result, ["extraction", "keyword", "Test"])
