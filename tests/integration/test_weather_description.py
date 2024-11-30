import unittest
from unittest.mock import patch, Mock
from src.services.weather_service import WeatherService

import requests

class TestWeatherServiceIntegration(unittest.TestCase):

    @patch('requests.get')
    def test_get_weather_by_location_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "weather": [{"description": "clear sky"}],
            "main": {"temp": 25, "humidity": 50},
            "wind": {"speed": 5.0}
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        location = {"city": "Toronto"}

        result = WeatherService.get_weather_by_location(location)

        # Assertions
        self.assertEqual(result["description"], "clear sky")
        self.assertEqual(result["temperature"], 25)
        self.assertEqual(result["humidity"], 50)
        self.assertEqual(result["wind_speed"], 5.0)
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_weather_by_location_failure(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Failure")
        mock_get.return_value = mock_response

        location = {"city": "InvalidCity"}

        result = WeatherService.get_weather_by_location(location)

        # Assertions
        self.assertEqual(result["description"], "Unknown")
        self.assertEqual(result["temperature"], 0)
        self.assertEqual(result["humidity"], 0)

    @patch('requests.get')
    def test_get_location_from_ip_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "city": "Toronto",
            "regionName": "Ontario",
            "country": "Canada",
            "lat": 43.7,
            "lon": -79.4
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        ip_address = "8.8.8.8"

        result = WeatherService.get_location_from_ip(ip_address)

        # Assertions
        self.assertEqual(result["city"], "Toronto")
        self.assertEqual(result["region"], "Ontario")
        self.assertEqual(result["country"], "Canada")
        self.assertEqual(result["latitude"], 43.7)
        self.assertEqual(result["longitude"], -79.4)

        mock_get.assert_called_once_with("http://ip-api.com/json/8.8.8.8")

    @patch('src.services.weather_service.requests.get')
    def test_get_location_from_ip_failure(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Failure")
        mock_get.return_value = mock_response

        ip_address = "InvalidIP"

        result = WeatherService.get_location_from_ip(ip_address)

        # Assertions
        self.assertEqual(result["city"], "Unknown")
        self.assertEqual(result["region"], "Unknown")
        self.assertEqual(result["country"], "Unknown")