from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .models import WeatherData, WeatherForecast
from .serializers import WeatherDataSerializer, WeatherForecastSerializer
from .services import OpenWeatherService


@extend_schema(tags=['Weather'])
class CurrentWeatherView(APIView):
    """Data cuaca terkini (data terbaru dari DB)"""
    permission_classes = [AllowAny]

    def get(self, request):
        latest = WeatherData.objects.first()
        if not latest:
            # Fallback: fetch langsung dari API jika DB kosong
            raw = OpenWeatherService.fetch_current()
            if raw:
                parsed = OpenWeatherService.parse_current(raw)
                return Response({
                    'source': 'openweather_live',
                    **parsed,
                })
            return Response({'error': 'Data cuaca tidak tersedia'}, status=503)
        serializer = WeatherDataSerializer(latest)
        return Response(serializer.data)


@extend_schema(tags=['Weather'])
class WeatherHistoryView(generics.ListAPIView):
    """Riwayat data cuaca (24 jam terakhir)"""
    serializer_class = WeatherDataSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        from django.utils import timezone
        from datetime import timedelta
        since = timezone.now() - timedelta(hours=24)
        return WeatherData.objects.filter(created_at__gte=since)[:48]


@extend_schema(tags=['Weather'])
class WeatherForecastView(generics.ListAPIView):
    """Prakiraan cuaca ke depan"""
    serializer_class = WeatherForecastSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        from django.utils import timezone
        return WeatherForecast.objects.filter(forecast_time__gte=timezone.now())[:8]
