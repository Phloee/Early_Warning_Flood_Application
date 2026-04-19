from django.db import models
from apps.areas.models import Area


class WeatherData(models.Model):
    """Data cuaca yang diambil dari BMKG atau WeatherAPI"""

    class Source(models.TextChoices):
        BMKG = 'bmkg', 'BMKG'
        OPENWEATHER = 'openweather', 'OpenWeatherMap'
        WEATHERAPI = 'weatherapi', 'WeatherAPI.com'

    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='weather_data',
        null=True, blank=True,
        help_text='Wilayah terkait (null = data umum Jakarta)',
    )
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.BMKG)
    temperature = models.FloatField(null=True, blank=True, help_text='Suhu dalam Celsius')
    humidity = models.IntegerField(null=True, blank=True, help_text='Kelembaban dalam %')
    rainfall = models.FloatField(default=0.0, help_text='Curah hujan dalam mm/jam')
    wind_speed = models.FloatField(null=True, blank=True, help_text='Kecepatan angin km/jam')
    description = models.CharField(max_length=255, blank=True, help_text='Deskripsi cuaca')
    weather_code = models.CharField(max_length=50, blank=True, help_text='Kode cuaca dari sumber')
    raw_data = models.JSONField(default=dict, help_text='Data mentah dari API')
    recorded_at = models.DateTimeField(help_text='Waktu data diambil')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'weather_data'
        verbose_name = 'Data Cuaca'
        verbose_name_plural = 'Data Cuaca'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['area', '-recorded_at']),
            models.Index(fields=['-recorded_at']),
        ]

    def __str__(self):
        area_name = self.area.name if self.area else 'Jakarta'
        return f'{area_name} – {self.description} ({self.recorded_at.strftime("%d/%m %H:%M")})'


class WeatherForecast(models.Model):
    """Prakiraan cuaca ke depan"""
    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='forecasts',
        null=True, blank=True,
    )
    source = models.CharField(max_length=20, default='openweather')
    forecast_time = models.DateTimeField(help_text='Waktu yang diprakirakan')
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.IntegerField(null=True, blank=True)
    rainfall_probability = models.IntegerField(default=0, help_text='Probabilitas hujan 0-100%')
    description = models.CharField(max_length=255, blank=True)
    raw_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'weather_forecasts'
        verbose_name = 'Prakiraan Cuaca'
        verbose_name_plural = 'Prakiraan Cuaca'
        ordering = ['forecast_time']

    def __str__(self):
        area_name = self.area.name if self.area else 'Jakarta'
        return f'Prakiraan {area_name} – {self.forecast_time.strftime("%d/%m %H:%M")}'
