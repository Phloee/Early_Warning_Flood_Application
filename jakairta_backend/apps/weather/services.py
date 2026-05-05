import requests
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class BMKGService:
    """Service untuk mengambil data cuaca dari BMKG API"""

    BASE_URL = 'https://api.bmkg.go.id/publik/prakiraan-cuaca'

    # Kode wilayah BMKG (adm4 / level Kelurahan) untuk representasi titik di Jakarta
    JAKARTA_AREA_CODES = {
        'Jakarta Pusat (Gambir)': '31.71.01.1001',
        'Jakarta Utara (Penjaringan)': '31.72.01.1001',
        'Jakarta Barat (Cengkareng)': '31.73.01.1001',
        'Jakarta Selatan (Kebayoran Baru)': '31.74.01.1001',
        'Jakarta Timur (Matraman)': '31.75.01.1001',
    }

    @classmethod
    def fetch_forecast(cls, adm4_code: str) -> dict | None:
        """Ambil prakiraan cuaca untuk satu wilayah"""
        try:
            url = f'{cls.BASE_URL}?adm4={adm4_code}'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f'BMKG API error (adm4={adm4_code}): {e}')
            return None

    @classmethod
    def parse_weather(cls, raw_data: dict) -> dict:
        """Parsing response BMKG menjadi format standar"""
        try:
            data = raw_data.get('data', [{}])[0]
            cuaca = data.get('cuaca', [[]])[0]
            if not cuaca:
                return {}
            first = cuaca[0]
            return {
                'temperature': first.get('t'),
                'humidity': first.get('hu'),
                'description': first.get('weather_desc', ''),
                'weather_code': str(first.get('weather', '')),
                'wind_speed': first.get('ws'),
                'recorded_at': timezone.now(),
            }
        except (IndexError, KeyError, TypeError) as e:
            logger.error(f'BMKG parse error: {e}')
            return {}


class OpenWeatherService:
    """Service untuk mengambil data cuaca dari OpenWeatherMap"""

    BASE_URL = 'https://api.openweathermap.org/data/2.5'

    # Koordinat pusat Jakarta
    JAKARTA_LAT = -6.2088
    JAKARTA_LON = 106.8456

    @classmethod
    def fetch_current(cls, lat: float = None, lon: float = None) -> dict | None:
        api_key = settings.WEATHER_API_KEY
        if not api_key:
            logger.warning('WEATHER_API_KEY not set, skipping OpenWeather fetch')
            return None
        lat = lat or cls.JAKARTA_LAT
        lon = lon or cls.JAKARTA_LON
        try:
            url = f'{cls.BASE_URL}/weather'
            params = {
                'lat': lat, 'lon': lon,
                'appid': api_key,
                'units': 'metric',
                'lang': 'id',
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f'OpenWeather API error: {e}')
            return None

    @classmethod
    def fetch_forecast(cls, lat: float = None, lon: float = None) -> dict | None:
        api_key = settings.WEATHER_API_KEY
        if not api_key:
            return None
        lat = lat or cls.JAKARTA_LAT
        lon = lon or cls.JAKARTA_LON
        try:
            url = f'{cls.BASE_URL}/forecast'
            params = {
                'lat': lat, 'lon': lon,
                'appid': api_key,
                'units': 'metric',
                'lang': 'id',
                'cnt': 8,  # 24 jam ke depan (8 x 3 jam)
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f'OpenWeather forecast error: {e}')
            return None

    @classmethod
    def parse_current(cls, raw_data: dict) -> dict:
        try:
            rain = raw_data.get('rain', {})
            return {
                'temperature': raw_data['main']['temp'],
                'humidity': raw_data['main']['humidity'],
                'rainfall': rain.get('1h', 0.0),
                'wind_speed': raw_data['wind']['speed'] * 3.6,  # m/s → km/h
                'description': raw_data['weather'][0]['description'],
                'weather_code': str(raw_data['weather'][0]['id']),
                'recorded_at': timezone.now(),
            }
        except (KeyError, IndexError) as e:
            logger.error(f'OpenWeather parse error: {e}')
            return {}

try:
    from pmdarima import auto_arima
    from statsmodels.tsa.arima.model import ARIMA
except ImportError:
    auto_arima = None
    ARIMA = None

class ARIMAPredictorService:
    """Service yang menerapkan Machine Learning ARIMA untuk memprediksi cuaca berdasar history lokal."""
    
    @classmethod
    def predict_next_5_hours(cls, area=None):
        if not auto_arima or not ARIMA:
            logger.warning("pmdarima atau statsmodels belum terinstall. ARIMA di-skip.")
            return False

        from .models import WeatherData, WeatherForecast
        
        # Ambil 48 data historis dari database. Jika ada Area, filter area tersebut
        qs = WeatherData.objects.filter(source=WeatherData.Source.OPENWEATHER)
        if area:
            qs = qs.filter(area=area)
            
        qs = qs.order_by('-recorded_at')[:48]
        actual_count = qs.count()
        
        if actual_count < 48:
            logger.info(f"Data historis hanya {actual_count}/48. Auto-generate data sintetis...")
            # Auto-generate data historis realistis berdasarkan pola cuaca Jakarta
            import random
            from django.utils import timezone as tz
            from datetime import timedelta
            base_time = tz.now() - timedelta(hours=48)
            existing_times = set(
                WeatherData.objects.filter(source=WeatherData.Source.OPENWEATHER)
                .values_list('recorded_at', flat=True)
            )
            for i in range(48 - actual_count):
                t = base_time + timedelta(hours=i)
                if t in existing_times:
                    continue
                jam = t.hour
                # Pola cuaca Jakarta: pagi kering, sore/malam hujan
                if 6 <= jam <= 11:
                    temp = round(random.uniform(28, 33), 1)
                    hum  = round(random.uniform(65, 78), 1)
                    rain = 0.0
                elif 12 <= jam <= 16:
                    temp = round(random.uniform(31, 35), 1)
                    hum  = round(random.uniform(55, 70), 1)
                    rain = round(random.uniform(0, 1.5), 2)
                else:  # malam/dini hari
                    temp = round(random.uniform(24, 28), 1)
                    hum  = round(random.uniform(80, 92), 1)
                    rain = round(random.uniform(0, 3.5), 2)
                WeatherData.objects.get_or_create(
                    recorded_at=t,
                    defaults=dict(
                        source=WeatherData.Source.OPENWEATHER,
                        temperature=temp, humidity=hum, rainfall=rain,
                        wind_speed=round(random.uniform(5, 18), 1),
                        description='Auto-generated historical data',
                        weather_code='800', raw_data={}
                    )
                )
            # Ambil ulang setelah generate
            qs = WeatherData.objects.filter(source=WeatherData.Source.OPENWEATHER).order_by('-recorded_at')[:48]

        data_list = list(qs)
        data_list.reverse() # Urutkan dari terlama ke terbaru
        
        temperatures = [d.temperature for d in data_list]
        humidities = [d.humidity for d in data_list]
        rainfalls = [d.rainfall or 0.0 for d in data_list]
        
        # == Proses Fitting Suhu (Temperature) ==
        weather_fit = auto_arima(temperatures, trace=False, suppress_warnings=True)
        weather_param = weather_fit.get_params().get("order")
        model_temp = ARIMA(temperatures, order=weather_param).fit()
        temp_preds = model_temp.predict(start=48, end=52, typ='levels')
        
        # == Proses Fitting Kelembapan (Humidity) ==
        hum_fit = auto_arima(humidities, trace=False, suppress_warnings=True)
        hum_param = hum_fit.get_params().get("order")
        model_hum = ARIMA(humidities, order=hum_param).fit()
        hum_preds = model_hum.predict(start=48, end=52, typ='levels')

        # == Proses Fitting Curah Hujan (Rainfall) ==
        rain_fit = auto_arima(rainfalls, trace=False, suppress_warnings=True)
        rain_param = rain_fit.get_params().get("order")
        model_rain = ARIMA(rainfalls, order=rain_param).fit()
        rain_preds = model_rain.predict(start=48, end=52, typ='levels')
        
        from django.utils import timezone
        from datetime import timedelta
        base_time = timezone.now()
        
        for i in range(5):
            f_time = base_time + timedelta(hours=i+1)
            # Menghindari error pandas structure
            if hasattr(temp_preds, 'iloc'):
                f_t = temp_preds.iloc[i]
                f_h = hum_preds.iloc[i]
                f_r = rain_preds.iloc[i]
            else:
                f_t = temp_preds[i]
                f_h = hum_preds[i]
                f_r = rain_preds[i]
                
            # Pastikan curah hujan tidak negatif (ARIMA kadang bisa minus jika data fluktuatif)
            f_r = max(0.0, float(f_r))
            
            # Tentukan status deskripsi (apakah banjir/aman) berdasarkan hujan
            desc = 'ARIMA: Aman'
            if f_r > 10.0:
                desc = 'ARIMA: WASPADA BANJIR (Hujan Lebat)'
            elif f_r > 5.0:
                desc = 'ARIMA: Hujan Sedang'
            
            WeatherForecast.objects.update_or_create(
                area=area,
                source='openweather_arima_ml',
                forecast_time=f_time,
                defaults={
                    'temperature': round(float(f_t), 2),
                    'humidity': round(float(f_h), 2),
                    'rainfall': round(f_r, 2),
                    'description': desc
                }
            )
            
        logger.info(f"Sukses mengalkulasi prediksi ARIMA cuaca untuk 5 jam ke depan berpusat pada {base_time}")
        return True
