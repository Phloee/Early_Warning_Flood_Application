import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.weather.tasks import fetch_and_save_current_weather
from apps.weather.services import ARIMAPredictorService

print("Fetching current weather from OpenWeather...")
fetch_and_save_current_weather()

print("Generating ARIMA predictions...")
# This will also generate synthetic historical data if needed
ARIMAPredictorService.predict_next_5_hours()

print("Dashboard data population complete.")
