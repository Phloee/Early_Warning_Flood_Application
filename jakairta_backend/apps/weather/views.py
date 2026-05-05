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
class WeatherForecastView(APIView):
    """Prakiraan cuaca ke depan menggunakan ARIMA dari titik Monas & Gambir"""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            import pandas as pd
            import numpy as np
            from django.utils import timezone as tz
            from datetime import timedelta
            from apps.weather.services import OpenWeatherService
            
            now = tz.now()
            
            JAKARTA_MONITOR_POINTS = [
                {'name': 'Monas',  'lat': -6.1754, 'lon': 106.8272},
                {'name': 'Gambir', 'lat': -6.1784, 'lon': 106.8316},
            ]
            
            live_points = []
            for point in JAKARTA_MONITOR_POINTS:
                try:
                    raw = OpenWeatherService.fetch_current(lat=point['lat'], lon=point['lon'])
                    if raw:
                        parsed = OpenWeatherService.parse_current(raw)
                        if parsed:
                            parsed['point'] = point['name']
                            live_points.append(parsed)
                except Exception:
                    pass

            # Ambil data historis
            qs = WeatherData.objects.all().order_by('-recorded_at')[:48]
            data_qs = list(qs)[::-1]
            if len(data_qs) < 5:
                # Baseline
                rainfall_raw = [0.0, 0.5, 2.5, 5.0, 10.0, 15.0, 5.0, 1.0, 0.0, 0.0] * 5
                temps_raw    = [26.0, 28.0, 31.0, 30.0, 28.0, 27.0, 26.0, 25.0, 25.5, 26.0] * 5
                humids_raw   = [85, 80, 70, 75, 80, 85, 90, 92, 90, 88] * 5
            else:
                rainfall_raw = [float(d.rainfall or 0.0) for d in data_qs]
                temps_raw    = [float(d.temperature) for d in data_qs if d.temperature is not None]
                humids_raw   = [float(d.humidity) for d in data_qs if d.humidity is not None]

            min_len = min(len(rainfall_raw), len(temps_raw), len(humids_raw))
            rainfall_raw = rainfall_raw[:min_len]
            temps_raw    = temps_raw[:min_len]
            humids_raw   = humids_raw[:min_len]

            # Fit ARIMA
            try:
                from pmdarima import auto_arima
                from statsmodels.tsa.arima.model import ARIMA
                
                def _predict(series):
                    if len(series) >= 10:
                        m = auto_arima(series, seasonal=False, suppress_warnings=True, error_action='ignore', max_p=3, max_q=2, d=0)
                        return m.predict(n_periods=5)
                    else:
                        m = ARIMA(series, order=(1,0,0)).fit()
                        return m.forecast(steps=5)
                        
                rain_forecast = list(_predict(pd.Series(rainfall_raw).fillna(0)))
                temp_forecast = list(_predict(pd.Series(temps_raw).fillna(29.0)))
                hum_forecast  = list(_predict(pd.Series(humids_raw).fillna(80.0)))
            except Exception:
                rain_forecast = [float(np.mean(rainfall_raw))] * 5
                temp_forecast = [float(np.mean(temps_raw))] * 5
                hum_forecast  = [float(np.mean(humids_raw))] * 5
                
            # Blend dengan data live
            if live_points:
                live_rain_avg = float(np.mean([p.get('rainfall', 0.0) for p in live_points]))
                live_temp_avg = float(np.mean([p.get('temperature', 29.0) for p in live_points]))
                live_hum_avg  = float(np.mean([p.get('humidity', 80.0) for p in live_points]))
                rain_forecast[0] = 0.7 * live_rain_avg + 0.3 * max(0, float(rain_forecast[0]))
                temp_forecast[0] = 0.7 * live_temp_avg + 0.3 * float(temp_forecast[0])
                hum_forecast[0]  = 0.7 * live_hum_avg  + 0.3 * float(hum_forecast[0])

            results = []
            for i in range(5):
                t = now + timedelta(hours=i+1)
                r = max(0.0, float(rain_forecast[i]))
                tp = round(float(temp_forecast[i]), 1)
                hm = round(float(hum_forecast[i]), 0)
                
                if r >= 50:
                    status, type_lbl = "Critical: Very Heavy Rain", "critical"
                elif r >= 20:
                    status, type_lbl = "Warning: Heavy Rain", "warning"
                elif r >= 10:
                    status, type_lbl = "Warning: Moderate Rain", "warning"
                else:
                    status, type_lbl = "Safe: Normal conditions", "safe"
                    
                results.append({
                    "time": t.strftime('%H:%M'),
                    "rainfall": round(r, 1),
                    "temperature": tp,
                    "humidity": hm,
                    "status": status,
                    "type": type_lbl
                })

            return Response({
                "success": True,
                "data": results,
                "live_points": [p['point'] for p in live_points]
            })

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=500)
