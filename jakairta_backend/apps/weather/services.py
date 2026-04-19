import requests
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class BMKGService:
    """Service untuk mengambil data cuaca dari BMKG API"""

    BASE_URL = 'https://api.bmkg.go.id/publik/prakiraan-cuaca'

    # Kode wilayah BMKG untuk Jakarta
    JAKARTA_AREA_CODES = {
        'Jakarta Pusat': '31.71.04',
        'Jakarta Utara': '31.71.01',
        'Jakarta Barat': '31.71.03',
        'Jakarta Selatan': '31.71.05',
        'Jakarta Timur': '31.71.02',
    }

    @classmethod
    def fetch_forecast(cls, adm4_code: str) -> dict | None:
        """Ambil prakiraan cuaca untuk satu wilayah"""
        try:
            url = f'{cls.BASE_URL}?adm4={adm4_code}'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f'BMKG API error (adm4={adm4_code}): {e}')
            return None

    @classmethod
    def parse_weather(cls, raw_data: dict) -> dict:
        """Parsing response BMKG menjadi format standar"""
        try:
            data = raw_data.get('data', [{}])[0]
            cuaca = data.get('cuaca', [[]])[0]
            if not cuaca:
                return {}
            first = cuaca[0]
            return {
                'temperature': first.get('t'),
                'humidity': first.get('hu'),
                'description': first.get('weather_desc', ''),
                'weather_code': str(first.get('weather', '')),
                'wind_speed': first.get('ws'),
                'recorded_at': timezone.now(),
            }
        except (IndexError, KeyError, TypeError) as e:
            logger.error(f'BMKG parse error: {e}')
            return {}


class OpenWeatherService:
    """Service untuk mengambil data cuaca dari OpenWeatherMap"""

    BASE_URL = 'https://api.openweathermap.org/data/2.5'

    # Koordinat pusat Jakarta
    JAKARTA_LAT = -6.2088
    JAKARTA_LON = 106.8456

    @classmethod
    def fetch_current(cls, lat: float = None, lon: float = None) -> dict | None:
        api_key = settings.WEATHER_API_KEY
        if not api_key:
            logger.warning('WEATHER_API_KEY not set, skipping OpenWeather fetch')
            return None
        lat = lat or cls.JAKARTA_LAT
        lon = lon or cls.JAKARTA_LON
        try:
            url = f'{cls.BASE_URL}/weather'
            params = {
                'lat': lat, 'lon': lon,
                'appid': api_key,
                'units': 'metric',
                'lang': 'id',
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f'OpenWeather API error: {e}')
            return None

    @classmethod
    def fetch_forecast(cls, lat: float = None, lon: float = None) -> dict | None:
        api_key = settings.WEATHER_API_KEY
        if not api_key:
            return None
        lat = lat or cls.JAKARTA_LAT
        lon = lon or cls.JAKARTA_LON
        try:
            url = f'{cls.BASE_URL}/forecast'
            params = {
                'lat': lat, 'lon': lon,
                'appid': api_key,
                'units': 'metric',
                'lang': 'id',
                'cnt': 8,  # 24 jam ke depan (8 x 3 jam)
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f'OpenWeather forecast error: {e}')
            return None

    @classmethod
    def parse_current(cls, raw_data: dict) -> dict:
        try:
            rain = raw_data.get('rain', {})
            return {
                'temperature': raw_data['main']['temp'],
                'humidity': raw_data['main']['humidity'],
                'rainfall': rain.get('1h', 0.0),
                'wind_speed': raw_data['wind']['speed'] * 3.6,  # m/s → km/h
                'description': raw_data['weather'][0]['description'],
                'weather_code': str(raw_data['weather'][0]['id']),
                'recorded_at': timezone.now(),
            }
        except (KeyError, IndexError) as e:
            logger.error(f'OpenWeather parse error: {e}')
            return {}
