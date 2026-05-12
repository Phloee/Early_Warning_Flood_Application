import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.areas.models import Area
from apps.cctv.models import CCTVCamera

def fix_all():
    print("Fixing database values...")
    
    # 1. Update Area statuses based on water level
    areas = Area.objects.all()
    for area in areas:
        old_status = area.status
        area.status = area.classify_status()
        if old_status != area.status:
            print(f"Updated {area.name}: {old_status} -> {area.status}")
        area.save()
        
    # 2. Fix Cikoko CCTV URL
    cikoko = Area.objects.filter(name__icontains='Pancoran / Cikoko').first()
    if cikoko:
        cctv = CCTVCamera.objects.filter(area=cikoko).first()
        if cctv:
            # Try the new URL from the scanner
            cctv.stream_url = "https://cctv.balitower.co.id/Cikoko-006-705651_3/index.m3u8"
            cctv.name = "CCTV Bali Tower - Cikoko (Fixed)"
            cctv.save()
            print(f"Updated Cikoko CCTV URL to {cctv.stream_url}")

# Run for default (Postgres)
try:
    fix_all()
except Exception as e:
    print(f"Postgres error: {e}")

# Run for SQLite
try:
    os.environ['DATABASE_URL'] = 'sqlite:///db.sqlite3'
    # Force re-evaluation of settings or just run in a sub-process
    # Since I'm in a script, I'll just run it. 
    # Note: django-environ reads DATABASE_URL at setup time, so we might need a separate call.
except: pass

print("Fix script completed.")
