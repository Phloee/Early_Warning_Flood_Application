import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.areas.models import Area, FloodStatus

areas_data = [
    {
        "name": "Kampung Melayu",
        "district": "Jakarta Timur",
        "sub_district": "Jatinegara",
        "latitude": -6.2280,
        "longitude": 106.8633,
        "status": FloodStatus.POTENSIAL,
        "water_level_cm": 85.0,
    },
    {
        "name": "Cipinang Melayu",
        "district": "Jakarta Timur",
        "sub_district": "Makasar",
        "latitude": -6.2492,
        "longitude": 106.9075,
        "status": FloodStatus.AMAN,
        "water_level_cm": 30.0,
    },
    {
        "name": "Pluit",
        "district": "Jakarta Utara",
        "sub_district": "Penjaringan",
        "latitude": -6.1130,
        "longitude": 106.7915,
        "status": FloodStatus.SIAGA,
        "water_level_cm": 120.0,
    },
    {
        "name": "Kelapa Gading",
        "district": "Jakarta Utara",
        "sub_district": "Kelapa Gading",
        "latitude": -6.1601,
        "longitude": 106.9006,
        "status": FloodStatus.AMAN,
        "water_level_cm": 10.0,
    },
    {
        "name": "Kemang",
        "district": "Jakarta Selatan",
        "sub_district": "Mampang Prapatan",
        "latitude": -6.2625,
        "longitude": 106.8166,
        "status": FloodStatus.AMAN,
        "water_level_cm": 15.0,
    },
    {
        "name": "Cikoko-006",
        "district": "Jakarta Selatan",
        "sub_district": "Pancoran",
        "latitude": -6.2447,
        "longitude": 106.8533,
        "status": FloodStatus.BANJIR,
        "water_level_cm": 185.0,
    },
]

for data in areas_data:
    area, created = Area.objects.update_or_create(
        name=data["name"],
        defaults={
            "district": data["district"],
            "sub_district": data["sub_district"],
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "status": data["status"],
            "water_level_cm": data["water_level_cm"],
        }
    )
    if created:
        print(f"Created area: {area.name}")
    else:
        print(f"Updated area: {area.name}")

print("Area population complete.")
