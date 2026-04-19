from django.apps import AppConfig


class WeatherConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.weather'
    verbose_name = 'Data Cuaca'

    def ready(self):
        """Start scheduler saat Django server siap"""
        import os
        # Hindari double-start di development (Django reload)
        if os.environ.get('RUN_MAIN') == 'true' or not os.environ.get('DJANGO_DEVELOPMENT'):
            try:
                from apps.weather.scheduler import start_scheduler
                start_scheduler()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f'Scheduler start failed: {e}')
