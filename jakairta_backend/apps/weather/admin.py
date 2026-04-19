from django.contrib import admin
from .models import WeatherData, WeatherForecast


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['area', 'source', 'temperature', 'humidity', 'rainfall', 'description', 'recorded_at']
    list_filter = ['source', 'recorded_at']
    ordering = ['-recorded_at']
    readonly_fields = ['raw_data', 'recorded_at', 'created_at']


@admin.register(WeatherForecast)
class WeatherForecastAdmin(admin.ModelAdmin):
    list_display = ['area', 'forecast_time', 'temperature', 'rainfall_probability', 'description']
    list_filter = ['source', 'forecast_time']
    ordering = ['forecast_time']
