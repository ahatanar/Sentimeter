import requests

class WeatherService:
    @staticmethod
    def get_weather_by_location(location):
        """
        Fetch weather data for a given location.
        :param location: Dictionary containing city or coordinates.
        :return: Weather details.
        """
        api_key = "your_openweathermap_api_key"
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
            return {"description": "Unknown", "temperature": 0, "humidity": 0, "wind_speed": 0}

   
        
    @staticmethod
    def get_location_from_ip(ip_address):
        """
        Fetch user's location based on IP address.
        :param ip_address: The IP address of the user.
        :return: Location details (e.g., city, region, country).
        """
        try:
            response = requests.get(f"http://ip-api.com/json/{ip_address}")
            response.raise_for_status()
            data = response.json()
            return {
                "city": data.get("city", "Unknown"),
                "region": data.get("regionName", "Unknown"),
                "country": data.get("country", "Unknown"),
                "latitude": data.get("lat"),
                "longitude": data.get("lon")
            }
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to fetch location: {e}")
            return {"city": "Unknown", "region": "Unknown", "country": "Unknown"}