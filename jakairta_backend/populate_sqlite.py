import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# Force SQLite for this script to match the running server
os.environ['DATABASE_URL'] = 'sqlite:///db.sqlite3'

django.setup()

from apps.areas.models import Area, FloodStatus
from apps.weather.models import WeatherData
from apps.cctv.models import CCTVCamera
from django.utils import timezone

print(f"Using database: {settings.DATABASES['default']['NAME']}")

# 1. Populate Areas
areas_data = [
    {"name": "Kampung Melayu", "district": "Jakarta Timur", "latitude": -6.2280, "longitude": 106.8633, "status": FloodStatus.POTENSIAL, "water_level_cm": 85.0},
    {"name": "Pluit", "district": "Jakarta Utara", "latitude": -6.1130, "longitude": 106.7915, "status": FloodStatus.SIAGA, "water_level_cm": 120.0},
    {"name": "Kemang", "district": "Jakarta Selatan", "latitude": -6.2625, "longitude": 106.8166, "status": FloodStatus.AMAN, "water_level_cm": 15.0},
    {"name": "Cikoko-006", "district": "Jakarta Selatan", "latitude": -6.2447, "longitude": 106.8533, "status": FloodStatus.BANJIR, "water_level_cm": 185.0},
]

for data in areas_data:
    Area.objects.update_or_create(
        name=data["name"],
        defaults={
            "district": data["district"],
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "status": data["status"],
            "water_level_cm": data["water_level_cm"],
            "is_active": True
        }
    )
print("Areas populated in SQLite.")

# 2. Populate CCTV
cctv_data = [
    {"area_name": "Kampung Melayu", "name": "Bendungan Jatinegara", "url": "https://cctv.balitower.co.id/Kelapa-Gading-015-700201_1/index.m3u8"},
    {"area_name": "Cikoko-006", "name": "Cikoko View", "url": "https://cctv.balitower.co.id/Pancoran-001-700431_1/index.m3u8"},
]

for data in cctv_data:
    try:
        area = Area.objects.get(name=data["area_name"])
        CCTVCamera.objects.update_or_create(
            name=data["name"],
            defaults={"area": area, "stream_url": data["url"], "is_active": True, "detection_result": "no_flood"}
        )
    except: pass
print("CCTV populated in SQLite.")

print("Done.")
