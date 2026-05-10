import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

print("Engine:", connection.settings_dict['ENGINE'])
print("DB Name:", connection.settings_dict['NAME'])
print("Host:", connection.settings_dict.get('HOST', ''))
print("Port:", connection.settings_dict.get('PORT', ''))

# Check if flood_analysis_logs table exists
with connection.cursor() as cursor:
    if 'postgresql' in connection.settings_dict['ENGINE']:
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;")
    else:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    print("\nAll tables:")
    for t in tables:
        print(f"  - {t}")

print("\nflood_analysis_logs exists:", 'flood_analysis_logs' in tables)
