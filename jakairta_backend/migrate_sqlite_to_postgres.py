"""
Script migrasi data dari SQLite ke PostgreSQL.
Jalankan: python migrate_sqlite_to_postgres.py
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import sqlite3
from apps.areas.models import Area
from apps.cctv.models import CCTVCamera, VideoSimulasi
from django.utils import timezone

sqlite_path = 'db.sqlite3'
if not os.path.exists(sqlite_path):
    print("ERROR: db.sqlite3 tidak ditemukan!")
    exit(1)

conn = sqlite3.connect(sqlite_path)
cur = conn.cursor()

# ── 1. Migrate Areas ──────────────────────────────────────────
print("\n=== Migrasi Areas ===")
cur.execute("SELECT id, name, district, sub_district, latitude, longitude, status, water_level_cm, water_level_change, description, is_active FROM areas")
for row in cur.fetchall():
    id_, name, district, sub_district, lat, lon, status, wl_cm, wl_change, desc, is_active = row
    obj, created = Area.objects.get_or_create(
        id=id_,
        defaults={
            'name': name,
            'district': district,
            'sub_district': sub_district or '',
            'latitude': lat or 0,
            'longitude': lon or 0,
            'status': status or 'aman',
            'water_level_cm': wl_cm or 0,
            'water_level_change': wl_change or 0,
            'description': desc or '',
            'is_active': bool(is_active),
        }
    )
    print(f"  {'✅ Dibuat' if created else '⚠️  Sudah ada'}: {name} ({district})")

# ── 2. Migrate CCTV Cameras ──────────────────────────────────
print("\n=== Migrasi CCTV Cameras ===")
cur.execute("SELECT id, area_id, name, location_description, stream_url, thumbnail_url, is_active, detection_result, confidence_score FROM cctv_cameras")
for row in cur.fetchall():
    id_, area_id, name, loc_desc, stream_url, thumb_url, is_active, det_result, conf = row
    area = Area.objects.filter(id=area_id).first()
    obj, created = CCTVCamera.objects.get_or_create(
        id=id_,
        defaults={
            'area': area,
            'name': name,
            'location_description': loc_desc or '',
            'stream_url': stream_url or '',
            'thumbnail_url': thumb_url or '',
            'is_active': bool(is_active),
            'detection_result': det_result or 'offline',
            'confidence_score': conf or 0.0,
        }
    )
    print(f"  {'✅ Dibuat' if created else '⚠️  Sudah ada'}: {name} (area: {area})")

# ── 3. Migrate VideoSimulasi ──────────────────────────────────
print("\n=== Migrasi Video Simulasi ===")
cur.execute("SELECT id, title, video_file, area_id, is_active FROM video_simulasi")
for row in cur.fetchall():
    id_, title, video_file, area_id, is_active = row
    area = Area.objects.filter(id=area_id).first()
    obj, created = VideoSimulasi.objects.get_or_create(
        id=id_,
        defaults={
            'title': title,
            'video_file': video_file,
            'area': area,
            'is_active': bool(is_active),
        }
    )
    print(f"  {'✅ Dibuat' if created else '⚠️  Sudah ada'}: {title}")

conn.close()

print("\n🎉 Migrasi selesai!")
print(f"   Areas     : {Area.objects.count()} data")
print(f"   CCTV      : {CCTVCamera.objects.count()} data")
print(f"   Simulasi  : {VideoSimulasi.objects.count()} data")
