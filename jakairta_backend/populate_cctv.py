import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.cctv.models import CCTVCamera
from apps.areas.models import Area
from django.db import connection

# Fix sequence if needed
with connection.cursor() as cursor:
    cursor.execute("SELECT setval('cctv_cameras_id_seq', COALESCE((SELECT MAX(id) FROM cctv_cameras), 1))")

# Sample CCTV URLs (from Balitower or others)
cctv_data = [
    {
        "area_name": "Kampung Melayu",
        "name": "Bendungan Jatinegara",
        "stream_url": "https://cctv.balitower.co.id/Kelapa-Gading-015-700201_1/index.m3u8",
        "detection_result": CCTVCamera.DetectionResult.MULAI_BANJIR,
        "confidence_score": 0.75,
    },
    {
        "area_name": "Pluit",
        "name": "Pintu Air Pluit",
        "stream_url": "https://cctv.balitower.co.id/Penjaringan-011-700145_1/index.m3u8",
        "detection_result": CCTVCamera.DetectionResult.NO_FLOOD,
        "confidence_score": 0.95,
    },
    {
        "area_name": "Kelapa Gading",
        "name": "Bulevar Kelapa Gading",
        "stream_url": "https://cctv.balitower.co.id/Kelapa-Gading-001-700185_1/index.m3u8",
        "detection_result": CCTVCamera.DetectionResult.NO_FLOOD,
        "confidence_score": 0.98,
    },
    {
        "area_name": "Kemang",
        "name": "Jl. Kemang Raya",
        "stream_url": "https://cctv.balitower.co.id/Mampang-Prapatan-005-700451_1/index.m3u8",
        "detection_result": CCTVCamera.DetectionResult.NO_FLOOD,
        "confidence_score": 0.90,
    },
]

for data in cctv_data:
    try:
        area = Area.objects.get(name=data["area_name"])
        camera, created = CCTVCamera.objects.update_or_create(
            name=data["name"],
            area=area,
            defaults={
                "stream_url": data["stream_url"],
                "detection_result": data["detection_result"],
                "confidence_score": data["confidence_score"],
            }
        )
        if created:
            print(f"Created CCTV: {camera.name} in {area.name}")
        else:
            print(f"Updated CCTV: {camera.name}")
    except Area.DoesNotExist:
        print(f"Area {data['area_name']} not found.")

print("CCTV population complete.")
