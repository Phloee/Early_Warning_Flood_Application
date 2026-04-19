import logging
from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore

logger = logging.getLogger(__name__)

scheduler = None


def poll_weather_job():
    """Job yang dijalankan setiap 60 detik untuk polling data cuaca"""
    from apps.weather.models import WeatherData
    from apps.weather.services import BMKGService, OpenWeatherService

    try:
        # Polling dari OpenWeatherMap (lebih reliable format-nya)
        raw = OpenWeatherService.fetch_current()
        if raw:
            parsed = OpenWeatherService.parse_current(raw)
            if parsed:
                WeatherData.objects.create(
                    source=WeatherData.Source.OPENWEATHER,
                    **parsed,
                    raw_data=raw,
                )
                logger.info(f'Weather data saved: {parsed.get("description")} | {parsed.get("temperature")}°C')

        # Polling dari BMKG untuk Jakarta Pusat
        bmkg_raw = BMKGService.fetch_forecast('31.71.04.1001')
        if bmkg_raw:
            parsed_bmkg = BMKGService.parse_weather(bmkg_raw)
            if parsed_bmkg:
                WeatherData.objects.create(
                    source=WeatherData.Source.BMKG,
                    **parsed_bmkg,
                    raw_data=bmkg_raw,
                )
                logger.info('BMKG weather data saved')

    except Exception as e:
        logger.error(f'Polling job error: {e}')


def start_scheduler():
    """Start APScheduler untuk background polling"""
    global scheduler
    if scheduler and scheduler.running:
        return

    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), 'default')

    scheduler.add_job(
        poll_weather_job,
        trigger='interval',
        seconds=60,
        id='poll_weather',
        name='Poll Weather Data (BMKG + OpenWeather)',
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=30,
    )

    scheduler.start()
    logger.info('Weather polling scheduler started (interval: 60s)')
