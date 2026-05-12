import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.areas.models import Area
from apps.cctv.models import CCTVCamera

def cleanup_db():
    print(f"Cleaning up database...")
    
    # 1. Delete "Cikoko-006"
    deleted_count, _ = Area.objects.filter(name="Cikoko-006").delete()
    print(f"Deleted {deleted_count} 'Cikoko-006' areas.")
    
    # 2. Find "Pancoran / Cikoko - Updated" or ID 1
    cikoko = Area.objects.filter(id=1).first() or Area.objects.filter(name="Pancoran / Cikoko - Updated").first()
    
    if cikoko:
        old_name = cikoko.name
        cikoko.name = "Pancoran / Cikoko - CCTV Bali Tower"
        cikoko.is_active = True
        cikoko.save()
        print(f"Renamed '{old_name}' to '{cikoko.name}'.")
        
        # 3. Ensure CCTV is linked and active
        # Check if there's already a CCTV for this area
        cctv = CCTVCamera.objects.filter(area=cikoko).first()
        if not cctv:
            # Create a new one if missing
            CCTVCamera.objects.create(
                area=cikoko,
                name="CCTV Bali Tower - Cikoko",
                stream_url="https://cctv.balitower.co.id/Pancoran-001-700431_1/index.m3u8",
                is_active=True,
                detection_result="no_flood"
            )
            print("Created new CCTV for Cikoko.")
        else:
            cctv.is_active = True
            cctv.name = "CCTV Bali Tower - Cikoko"
            cctv.stream_url = "https://cctv.balitower.co.id/Pancoran-001-700431_1/index.m3u8"
            cctv.save()
            print("Updated existing CCTV for Cikoko.")
    else:
        print("Could not find Cikoko area to update.")

# Run for default (Postgres)
cleanup_db()

# Run for SQLite as well
os.environ['DATABASE_URL'] = 'sqlite:///db.sqlite3'
# We need to re-setup/reload settings? Django usually doesn't like changing DB on the fly like this
# But since settings.DATABASES is already populated, we can try to force it or just run another process
print("\nSwitching to SQLite...")
# A better way is to run another process
