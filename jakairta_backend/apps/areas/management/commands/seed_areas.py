from django.core.management.base import BaseCommand
from apps.areas.models import Area, FloodStatus


JAKARTA_AREAS = [
    # Jakarta Pusat
    {'name': 'Gambir', 'district': 'Jakarta Pusat', 'sub_district': 'Gambir', 'latitude': -6.1731, 'longitude': 106.8244, 'status': FloodStatus.AMAN, 'water_level_cm': 12.0},
    {'name': 'Tanah Abang', 'district': 'Jakarta Pusat', 'sub_district': 'Tanah Abang', 'latitude': -6.2057, 'longitude': 106.8118, 'status': FloodStatus.POTENSIAL, 'water_level_cm': 65.0},
    {'name': 'Menteng', 'district': 'Jakarta Pusat', 'sub_district': 'Menteng', 'latitude': -6.1944, 'longitude': 106.8319, 'status': FloodStatus.AMAN, 'water_level_cm': 8.0},
    {'name': 'Senen', 'district': 'Jakarta Pusat', 'sub_district': 'Senen', 'latitude': -6.1771, 'longitude': 106.8457, 'status': FloodStatus.AMAN, 'water_level_cm': 20.0},

    # Jakarta Timur
    {'name': 'Kampung Melayu', 'district': 'Jakarta Timur', 'sub_district': 'Jatinegara', 'latitude': -6.2223, 'longitude': 106.8713, 'status': FloodStatus.BANJIR, 'water_level_cm': 180.0, 'water_level_change': 45.0},
    {'name': 'Bidara Cina', 'district': 'Jakarta Timur', 'sub_district': 'Jatinegara', 'latitude': -6.2174, 'longitude': 106.8786, 'status': FloodStatus.BANJIR, 'water_level_cm': 155.0, 'water_level_change': 30.0},
    {'name': 'Bukit Duri', 'district': 'Jakarta Timur', 'sub_district': 'Tebet', 'latitude': -6.2312, 'longitude': 106.8542, 'status': FloodStatus.POTENSIAL, 'water_level_cm': 95.0},
    {'name': 'Cawang', 'district': 'Jakarta Timur', 'sub_district': 'Kramat Jati', 'latitude': -6.2444, 'longitude': 106.8699, 'status': FloodStatus.AMAN, 'water_level_cm': 25.0},

    # Jakarta Selatan
    {'name': 'Kemang', 'district': 'Jakarta Selatan', 'sub_district': 'Mampang', 'latitude': -6.2608, 'longitude': 106.8141, 'status': FloodStatus.POTENSIAL, 'water_level_cm': 70.0},
    {'name': 'Cipete', 'district': 'Jakarta Selatan', 'sub_district': 'Pesanggrahan', 'latitude': -6.2730, 'longitude': 106.7972, 'status': FloodStatus.AMAN, 'water_level_cm': 15.0},
    {'name': 'Lebak Bulus', 'district': 'Jakarta Selatan', 'sub_district': 'Cilandak', 'latitude': -6.2886, 'longitude': 106.7759, 'status': FloodStatus.AMAN, 'water_level_cm': 10.0},

    # Jakarta Barat
    {'name': 'Grogol', 'district': 'Jakarta Barat', 'sub_district': 'Grogol Petamburan', 'latitude': -6.1666, 'longitude': 106.7906, 'status': FloodStatus.AMAN, 'water_level_cm': 30.0},
    {'name': 'Kembangan', 'district': 'Jakarta Barat', 'sub_district': 'Kembangan', 'latitude': -6.1935, 'longitude': 106.7414, 'status': FloodStatus.POTENSIAL, 'water_level_cm': 80.0},
    {'name': 'Kalideres', 'district': 'Jakarta Barat', 'sub_district': 'Kalideres', 'latitude': -6.1366, 'longitude': 106.6983, 'status': FloodStatus.AMAN, 'water_level_cm': 22.0},

    # Jakarta Utara
    {'name': 'Kelapa Gading', 'district': 'Jakarta Utara', 'sub_district': 'Kelapa Gading', 'latitude': -6.1600, 'longitude': 106.9050, 'status': FloodStatus.POTENSIAL, 'water_level_cm': 60.0},
    {'name': 'Pluit', 'district': 'Jakarta Utara', 'sub_district': 'Penjaringan', 'latitude': -6.1234, 'longitude': 106.7988, 'status': FloodStatus.AMAN, 'water_level_cm': 35.0},
    {'name': 'Tanjung Priok', 'district': 'Jakarta Utara', 'sub_district': 'Tanjung Priok', 'latitude': -6.1100, 'longitude': 106.8706, 'status': FloodStatus.AMAN, 'water_level_cm': 18.0},
    {'name': 'Muara Baru', 'district': 'Jakarta Utara', 'sub_district': 'Penjaringan', 'latitude': -6.1069, 'longitude': 106.8047, 'status': FloodStatus.POTENSIAL, 'water_level_cm': 90.0},
]


class Command(BaseCommand):
    help = 'Seed data awal wilayah Jakarta untuk Early Warning Flood System'

    def handle(self, *args, **kwargs):
        created = 0
        updated = 0
        for area_data in JAKARTA_AREAS:
            area_data.setdefault('water_level_change', 0.0)
            area_data.setdefault('description', '')
            obj, is_created = Area.objects.update_or_create(
                name=area_data['name'],
                district=area_data['district'],
                defaults=area_data,
            )
            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Seed selesai: {created} wilayah dibuat, {updated} wilayah diperbarui'
            )
        )
