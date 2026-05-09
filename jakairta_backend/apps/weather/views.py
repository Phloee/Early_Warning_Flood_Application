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
    """Prakiraan cuaca real-time dari OpenWeather Forecast API (3-jam interval)"""
    permission_classes = [AllowAny]

    HARI_ID = {
        'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
        'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu',
    }

    def get(self, request):
        try:
            import pytz
            from datetime import datetime

            wib = pytz.timezone('Asia/Jakarta')
            now_wib = datetime.now(wib)

            # Koordinat pusat Jakarta
            lat, lon = -6.2088, 106.8456

            raw_forecast = OpenWeatherService.fetch_forecast(lat=lat, lon=lon)

            if raw_forecast and 'list' in raw_forecast:
                items = raw_forecast['list'][:8]  # maks 8 slot (24 jam ke depan)
                results = []
                for item in items:
                    dt_utc = datetime.utcfromtimestamp(item['dt']).replace(tzinfo=pytz.utc)
                    dt_wib = dt_utc.astimezone(wib)

                    day_en  = dt_wib.strftime('%A')
                    day_id  = self.HARI_ID.get(day_en, day_en)
                    date_str = dt_wib.strftime('%d/%m')
                    time_str = dt_wib.strftime('%H:%M')

                    rain_3h = item.get('rain', {}).get('3h', 0.0)
                    temp    = round(item['main']['temp'], 1)
                    hum     = item['main']['humidity']
                    clouds  = item.get('clouds', {}).get('all', 0)

                    if rain_3h >= 50:
                        status, type_lbl = "Hujan Sangat Lebat", "critical"
                    elif rain_3h >= 20:
                        status, type_lbl = "Hujan Lebat", "warning"
                    elif rain_3h >= 5:
                        status, type_lbl = "Hujan Sedang", "warning"
                    elif rain_3h > 0:
                        status, type_lbl = "Hujan Ringan", "safe"
                    else:
                        status, type_lbl = "Tidak Hujan", "safe"

                    results.append({
                        "day":         day_id,
                        "date":        date_str,
                        "time":        time_str,
                        "rainfall":    round(rain_3h, 1),
                        "temperature": temp,
                        "humidity":    hum,
                        "cloud_pct":   clouds,
                        "status":      status,
                        "type":        type_lbl,
                    })

                return Response({
                    "success": True,
                    "source": "openweather_forecast",
                    "generated_at": now_wib.strftime('%d/%m/%Y %H:%M WIB'),
                    "data": results,
                })

            # Fallback ARIMA jika OW tidak tersedia
            return self._arima_fallback(wib)

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=500)

    def _arima_fallback(self, wib):
        import numpy as np
        import pandas as pd
        from datetime import datetime
        from django.utils import timezone as tz
        from datetime import timedelta

        now = tz.now()
        qs = WeatherData.objects.all().order_by('-recorded_at')[:48]
        data_qs = list(qs)[::-1]

        if len(data_qs) < 5:
            rainfall_raw = [0.0, 0.5, 2.5, 5.0, 10.0] * 10
            temps_raw    = [27.0, 29.0, 31.0, 28.0, 26.0] * 10
            humids_raw   = [80, 75, 70, 80, 85] * 10
        else:
            rainfall_raw = [float(d.rainfall or 0.0) for d in data_qs]
            temps_raw    = [float(d.temperature) for d in data_qs if d.temperature is not None]
            humids_raw   = [float(d.humidity) for d in data_qs if d.humidity is not None]

        min_len = min(len(rainfall_raw), len(temps_raw), len(humids_raw))
        try:
            from pmdarima import auto_arima
            def _predict(series):
                m = auto_arima(series, seasonal=False, suppress_warnings=True, error_action='ignore')
                return list(m.predict(n_periods=5))
            rain_f = _predict(pd.Series(rainfall_raw[:min_len]).fillna(0))
            temp_f = _predict(pd.Series(temps_raw[:min_len]).fillna(29.0))
            hum_f  = _predict(pd.Series(humids_raw[:min_len]).fillna(80.0))
        except Exception:
            rain_f = [float(np.mean(rainfall_raw[:min_len]))] * 5
            temp_f = [float(np.mean(temps_raw[:min_len]))] * 5
            hum_f  = [float(np.mean(humids_raw[:min_len]))] * 5

        results = []
        for i in range(5):
            t = now + timedelta(hours=i+1)
            t_wib = t.astimezone(wib)
            day_id = self.HARI_ID.get(t_wib.strftime('%A'), t_wib.strftime('%A'))
            r = round(max(0.0, float(rain_f[i])), 1)
            tp = round(float(temp_f[i]), 1)
            hm = round(float(hum_f[i]))
            if r >= 20: status, lbl = "Hujan Lebat", "warning"
            elif r >= 5: status, lbl = "Hujan Sedang", "warning"
            elif r > 0: status, lbl = "Hujan Ringan", "safe"
            else: status, lbl = "Tidak Hujan", "safe"
            results.append({
                "day": day_id, "date": t_wib.strftime('%d/%m'),
                "time": t_wib.strftime('%H:%M'),
                "rainfall": r, "temperature": tp, "humidity": hm,
                "cloud_pct": 0, "status": status, "type": lbl,
            })
        now_wib = now.astimezone(wib)
        return Response({
            "success": True, "source": "arima_fallback",
            "generated_at": now_wib.strftime('%d/%m/%Y %H:%M WIB'),
            "data": results,
        })


@extend_schema(tags=['Weather'])
class LiveWeatherView(APIView):
    """Cuaca real-time per koordinat untuk halaman detail Flutter"""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            lat = float(request.query_params.get('lat', -6.2297))
            lon = float(request.query_params.get('lon', 106.8599))
        except (ValueError, TypeError):
            return Response({'error': 'lat/lon tidak valid'}, status=400)

        try:
            raw = OpenWeatherService.fetch_current(lat=lat, lon=lon)
            if not raw:
                return Response({'error': 'Gagal ambil data OpenWeather'}, status=503)

            parsed = OpenWeatherService.parse_current(raw)

            # Extra fields for flood detection
            rain_1h = raw.get('rain', {}).get('1h', 0.0)
            rain_3h = raw.get('rain', {}).get('3h', 0.0)
            wind_speed = raw.get('wind', {}).get('speed', 0.0)   # m/s
            wind_deg   = raw.get('wind', {}).get('deg', 0)
            pressure   = raw.get('main', {}).get('pressure', 0)   # hPa
            visibility = raw.get('visibility', 10000)              # meters
            cloud_pct  = raw.get('clouds', {}).get('all', 0)      # %
            humidity   = raw.get('main', {}).get('humidity', 0)
            feels_like = raw.get('main', {}).get('feels_like', 0)
            weather_desc = raw.get('weather', [{}])[0].get('description', '')
            weather_icon = raw.get('weather', [{}])[0].get('icon', '')
            city_name  = raw.get('name', '')

            # Flood risk score (simple heuristic)
            flood_score = 0
            if rain_1h >= 10: flood_score += 40
            elif rain_1h >= 5: flood_score += 20
            elif rain_1h > 0: flood_score += 10
            if humidity >= 90: flood_score += 20
            elif humidity >= 80: flood_score += 10
            if cloud_pct >= 80: flood_score += 15
            if pressure < 1005: flood_score += 15
            if wind_speed >= 10: flood_score += 10

            if flood_score >= 60:
                flood_risk_label = 'TINGGI'
                flood_risk_color = 'red'
            elif flood_score >= 35:
                flood_risk_label = 'SEDANG'
                flood_risk_color = 'orange'
            else:
                flood_risk_label = 'RENDAH'
                flood_risk_color = 'green'

            return Response({
                'success': True,
                'city': city_name,
                'temperature': parsed.get('temperature'),
                'feels_like': round(feels_like - 273.15, 1) if feels_like > 100 else feels_like,
                'humidity': humidity,
                'description': weather_desc,
                'icon': f"https://openweathermap.org/img/wn/{weather_icon}@2x.png" if weather_icon else '',
                'rain_1h': round(rain_1h, 2),
                'rain_3h': round(rain_3h, 2),
                'wind_speed': round(wind_speed * 3.6, 1),  # convert m/s to km/h
                'wind_deg': wind_deg,
                'pressure': pressure,
                'visibility_km': round(visibility / 1000, 1),
                'cloud_pct': cloud_pct,
                'flood_risk_score': flood_score,
                'flood_risk_label': flood_risk_label,
                'flood_risk_color': flood_risk_color,
            })
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=500)
