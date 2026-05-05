import logging
from datetime import timedelta
from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.conf import settings
from apps.weather.models import WeatherData
from apps.weather.services import OpenWeatherService, ARIMAPredictorService

logger = logging.getLogger(__name__)

def fetch_and_save_current_weather():
    """Job rutin untuk merekam cuaca OpenWeather setiap jam dan memicu ML"""
    try:
        lat, lon = OpenWeatherService.JAKARTA_LAT, OpenWeatherService.JAKARTA_LON
        raw_data = OpenWeatherService.fetch_current(lat, lon)
        if raw_data:
            parsed = OpenWeatherService.parse_current(raw_data)
            if parsed:
                WeatherData.objects.create(
                    area=None,
                    source=WeatherData.Source.OPENWEATHER,
                    temperature=parsed.get('temperature'),
                    humidity=parsed.get('humidity'),
                    rainfall=parsed.get('rainfall', 0.0),
                    wind_speed=parsed.get('wind_speed'),
                    description=parsed.get('description', ''),
                    weather_code=parsed.get('weather_code', ''),
                    raw_data=raw_data,
                    recorded_at=parsed.get('recorded_at') or timezone.now()
                )
                logger.info("Rutin OpenWeatherMap: Data cuaca terbaru berhasil ditarik & disimpan.")
                
                # Coba menyalakan mesin prediktor ARIMA
                # Prediktor akan otomatis batal jika data kurang dari 48 jam
                ARIMAPredictorService.predict_next_5_hours()
    except Exception as e:
        logger.error(f"Error scheduler OpenWeather rutin: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Jadwalkan fungsi fetch_and_save_current_weather berjalan otomatis
    # interval = minutes=60 jika di server produksi, diubah jadi cepat buat test awal
    scheduler.add_job(
        fetch_and_save_current_weather,
        "interval",
        minutes=60, 
        id="fetch_openweather_hourly",
        replace_existing=True,
        misfire_grace_time=15*60
    )
    
    scheduler.start()
    logger.info("Background Scheduler untuk API & ML Cuaca berhasil dimulai...")
