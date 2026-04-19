from django.urls import path
from .views import CurrentWeatherView, WeatherHistoryView, WeatherForecastView

urlpatterns = [
    path('current/', CurrentWeatherView.as_view(), name='weather-current'),
    path('history/', WeatherHistoryView.as_view(), name='weather-history'),
    path('forecast/', WeatherForecastView.as_view(), name='weather-forecast'),
]
