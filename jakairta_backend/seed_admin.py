import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.areas.models import Area, FloodStatus
from apps.cctv.models import CCTVCamera
from apps.weather.models import WeatherForecast

User = get_user_model()

def seed():
    print("Menyiapkan data untuk Django Admin...")
    
    # 1. Buat Superuser
    if not User.objects.filter(email='admin@admin.com').exists():
        User.objects.create_superuser('admin@admin.com', 'admin123', name='Admin Utama')
        print("Superuser 'admin@admin.com' (pass: admin123) dibuat.")

    # 2. Buat Area
    area, created = Area.objects.get_or_create(
        name='Pancoran / Cikoko',
        defaults={'district': 'Jakarta Selatan', 'water_level_cm': 0.0, 'status': FloodStatus.AMAN, 'latitude': 0.0, 'longitude': 0.0}
    )
    
    CCTVCamera.objects.get_or_create(
        id=1,
        defaults={
            'area': area,
            'name': 'CCTV Cikoko-006',
            'stream_url': 'https://cctv.balitower.co.id/Cikoko-006-705651_3/embed.html',
            'detection_result': CCTVCamera.DetectionResult.FLOOD, # Sengaja disetting banjir untuk demo
            'confidence_score': 0.95
        }
    )
    
    # 4. Buat Weather Forecast (Hujan Lebat)
    WeatherForecast.objects.get_or_create(
        area=area,
        forecast_time=timezone.now() + timezone.timedelta(hours=1),
        defaults={
            'temperature': 28.0,
            'humidity': 90.0,
            'description': 'Rain',
            'rainfall': 15.5 # > 10 mm (Hujan Lebat)
        }
    )
    
    print("Data siap! Area dalam kondisi Siaga (Hujan & CCTV Banjir).")

if __name__ == '__main__':
    seed()
