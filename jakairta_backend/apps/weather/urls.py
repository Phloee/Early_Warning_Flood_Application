from django.urls import path
from .views import CurrentWeatherView, WeatherHistoryView, WeatherForecastView, LiveWeatherView

urlpatterns = [
    path('current/', CurrentWeatherView.as_view(), name='weather-current'),
    path('history/', WeatherHistoryView.as_view(), name='weather-history'),
    path('forecast/', WeatherForecastView.as_view(), name='weather-forecast'),
    path('live/', LiveWeatherView.as_view(), name='weather-live'),
]
