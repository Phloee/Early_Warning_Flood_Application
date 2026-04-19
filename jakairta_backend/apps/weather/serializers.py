from rest_framework import serializers
from .models import WeatherData, WeatherForecast


class WeatherDataSerializer(serializers.ModelSerializer):
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    area_name = serializers.CharField(source='area.name', read_only=True, default='Jakarta')

    class Meta:
        model = WeatherData
        fields = [
            'id', 'area_name', 'source', 'source_display',
            'temperature', 'humidity', 'rainfall', 'wind_speed',
            'description', 'weather_code', 'recorded_at',
        ]


class WeatherForecastSerializer(serializers.ModelSerializer):
    area_name = serializers.CharField(source='area.name', read_only=True, default='Jakarta')

    class Meta:
        model = WeatherForecast
        fields = [
            'id', 'area_name', 'source',
            'forecast_time', 'temperature', 'humidity',
            'rainfall_probability', 'description',
        ]
