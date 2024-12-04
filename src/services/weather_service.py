import requests
import os
from random import random
WEATHER_KEY = os.getenv("WEATHER_KEY")
LOCATION_KEY= os.getenv("LOCATION_KEY")

class WeatherService:
    
    @staticmethod
    def get_weather_by_location(location):
        """
        Fetch weather data using latitude/longitude or city name.
        :param location: Dictionary with latitude/longitude or city name.
        :return: Dictionary containing weather details.
        """
        api_key = WEATHER_KEY

        if "latitude" in location and "longitude" in location:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={location['latitude']}&lon={location['longitude']}&units=metric&appid={api_key}"
        else:
            if location.get('city', 'unknown') == "unknown":
                location['city'] = random.choice(
                    ["New York", "Beijing", "Oshawa", "Toronto", "Vatican City", 
                     "London", "Birmingham", "Miami", "Palo Alto", "Sacramento", 
                     "Austin", "Houston", "Seattle"]
                )
            url = f"https://api.openweathermap.org/data/2.5/weather?q={location['city']}&units=metric&appid={api_key}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return {
                "description": data["weather"][0]["description"],
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"]
            }
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to fetch weather: {e}")
            return {
                "description": "Unknown",
                "temperature": 0,
                "humidity": 0,
                "wind_speed": 0
            }


    @staticmethod
    def get_location_from_ip(ip_address):
        """
        Fetch user's location based on IP address.
        :param ip_address: The IP address of the user.
        :return: Location details (e.g., city, region, country).
        """
        print(ip_address)
        try:
            response = requests.get(f"http://ip-api.com/json/{ip_address}")
            response.raise_for_status()
            data = response.json()
            return {
                "city": data.get("city", "Unknown"),
                "region": data.get("regionName", "Unknown"),
                "country": data.get("country", "Unknown"),
                "latitude": str(data.get("lat","unknown")),
                "longitude": str(data.get("lon","unknown"))
            }
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to fetch location: {e}")
            return {"city": "Unknown", "region": "Unknown", "country": "Unknown"}
    @staticmethod
    def reverse_geocode(lat, lon):
        """
        Convert latitude and longitude into a structured location.
        :param lat: Latitude of the location.
        :param lon: Longitude of the location.
        :return: Dictionary with city, region, country, latitude, and longitude.
        """
        api_key = LOCATION_KEY
        url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={api_key}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if data['results']:
                location = data['results'][0]['components']
                return {
                    "city": location.get("city", location.get("town", location.get("village", "Unknown"))),
                    "region": location.get("state", "Unknown"),
                    "country": location.get("country", "Unknown"),
                    "latitude": str(lat),
                    "longitude": str(lon)
                }
            else:
                return {
                    "city": "Unknown",
                    "region": "Unknown",
                    "country": "Unknown",
                    "latitude": str(lat),
                    "longitude": str(lon)
                }
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to fetch reverse geocoding data: {e}")
            return {
                "city": "Unknown",
                "region": "Unknown",
                "country": "Unknown",
                "latitude": str(lat),
                "longitude": str(lon)
            }