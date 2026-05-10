"""
Database-Driven Accuracy Engine Injector
Tambahkan fungsi get_db_calibrated_thresholds() ke views.py
Fungsi ini menggunakan FloodAnalysisLog untuk belajar dari riwayat
dan mengkalibrasi threshold YOLO + HSV secara otomatis.
"""

new_engine = '''

# ══════════════════════════════════════════════════════════════
#  DATABASE ACCURACY ENGINE
#  Belajar dari riwayat FloodAnalysisLog untuk mengkalibrasi
#  threshold AI secara otomatis — semakin banyak data, semakin akurat
# ══════════════════════════════════════════════════════════════

def get_db_calibrated_thresholds(camera=None, area=None, hour_of_day=None,
                                  base_conf=0.62, base_hsv=0.40):
    """
    Hitung threshold YOLO confidence & HSV dinamis berdasarkan riwayat database.

    Algoritma:
    1. Ambil log terakhir 100 entri untuk kamera/area ini
    2. Hitung "false positive proxy": deteksi air dengan rasio < 5% dianggap mencurigakan
    3. Hitung "precision_score": seberapa sering deteksi benar-benar banjir besar
    4. Sesuaikan threshold: lokasi banyak FP → threshold lebih ketat
    5. Sesuaikan berdasarkan jam: jika jam ini historis sering AMAN, threshold naik

    Returns: (yolo_conf, hsv_min_ratio, stats_dict)
    """
    try:
        from apps.cctv.models import FloodAnalysisLog
        from django.utils import timezone as tz
        from datetime import timedelta

        stats = {
            'total_logs': 0,
            'flood_rate': 0.0,
            'fp_proxy_rate': 0.0,
            'hour_flood_rate': 0.0,
            'calibration_source': 'default',
        }

        # Query riwayat untuk kamera/area ini (100 log terakhir)
        qs = FloodAnalysisLog.objects.all()
        if camera:
            qs = qs.filter(camera=camera)
        elif area:
            qs = qs.filter(area=area)

        total = qs.count()
        stats['total_logs'] = total

        # Belum cukup data — gunakan default
        if total < 5:
            stats['calibration_source'] = 'default (data < 5)'
            return base_conf, base_hsv, stats

        recent = qs.order_by('-analyzed_at')[:100]

        # ── 1. Hitung flood rate keseluruhan ──
        flood_count = recent.filter(is_flood=True).count()
        flood_rate = flood_count / min(total, 100)
        stats['flood_rate'] = round(flood_rate * 100, 1)

        # ── 2. False Positive Proxy ──
        # Deteksi "water" dengan ratio sangat kecil (<5%) = kemungkinan false positive
        fp_proxy = recent.filter(has_water=True, water_area_ratio__lt=5.0).count()
        total_water = recent.filter(has_water=True).count()
        fp_rate = (fp_proxy / total_water) if total_water > 0 else 0.0
        stats['fp_proxy_rate'] = round(fp_rate * 100, 1)

        # ── 3. Pola jam-an (jika hour_of_day disediakan) ──
        if hour_of_day is not None:
            same_hour = recent.filter(analyzed_at__hour=hour_of_day)
            hour_total = same_hour.count()
            if hour_total >= 3:
                hour_flood = same_hour.filter(is_flood=True).count()
                hour_flood_rate = hour_flood / hour_total
                stats['hour_flood_rate'] = round(hour_flood_rate * 100, 1)
                # Jika pada jam ini hampir tidak pernah banjir (<10%), naikkan threshold
                if hour_flood_rate < 0.10:
                    base_conf = min(0.82, base_conf + 0.12)
                    base_hsv  = min(0.65, base_hsv  + 0.15)
                    stats['calibration_source'] = f'jam-{hour_of_day} jarang banjir'

        # ── 4. Kalibrasi berdasarkan FP rate ──
        if fp_rate > 0.75:
            # Sangat banyak false positive → threshold sangat ketat
            conf = min(0.85, base_conf + 0.18)
            hsv  = min(0.70, base_hsv  + 0.22)
            stats['calibration_source'] = 'DB: FP sangat tinggi (>75%)'
        elif fp_rate > 0.50:
            conf = min(0.78, base_conf + 0.12)
            hsv  = min(0.60, base_hsv  + 0.15)
            stats['calibration_source'] = 'DB: FP tinggi (50-75%)'
        elif fp_rate > 0.25:
            conf = min(0.72, base_conf + 0.06)
            hsv  = min(0.52, base_hsv  + 0.08)
            stats['calibration_source'] = 'DB: FP sedang (25-50%)'
        else:
            # FP rendah → model akurat di lokasi ini → bisa sedikit lebih sensitif
            conf = max(0.55, base_conf - 0.05)
            hsv  = max(0.30, base_hsv  - 0.05)
            stats['calibration_source'] = 'DB: Akurasi tinggi (FP <25%)'

        # ── 5. Bonus: jika flood_rate tinggi → jangan terlalu ketat ──
        if flood_rate > 0.50:
            conf = max(base_conf, conf - 0.08)  # Lokasi rawan, jangan terlalu ketat
            hsv  = max(base_hsv, hsv - 0.08)
            stats['calibration_source'] += ' + lokasi rawan banjir'

        return round(conf, 3), round(hsv, 3), stats

    except Exception as e:
        return base_conf, base_hsv, {'error': str(e), 'calibration_source': 'error-fallback'}


def get_water_confidence_score(water_area_ratio, hsv_passed, yolo_conf,
                                area=None, camera=None):
    """
    Hitung confidence akhir deteksi air, mempertimbangkan:
    - Rasio area genangan
    - Apakah HSV valid
    - YOLO confidence
    - Riwayat database di lokasi ini (precision correction)

    Returns: (final_score_pct, verdict)
    """
    try:
        from apps.cctv.models import FloodAnalysisLog

        # Base score dari YOLO + area
        base_score = (yolo_conf * 0.4) + (min(water_area_ratio / 100, 1.0) * 0.6)

        # Ambil precision dari DB untuk lokasi ini
        qs = FloodAnalysisLog.objects.filter(is_flood=True)
        if camera:
            qs = qs.filter(camera=camera)
        elif area:
            qs = qs.filter(area=area)

        total_qs = FloodAnalysisLog.objects.filter(has_water=True)
        if camera:
            total_qs = total_qs.filter(camera=camera)
        elif area:
            total_qs = total_qs.filter(area=area)

        true_pos = qs.count()
        all_water = total_qs.count()

        # Precision = berapa % deteksi air yang benar-benar banjir
        precision = (true_pos / all_water) if all_water >= 5 else 0.5

        # Adjusted score
        adjusted = base_score * (0.5 + precision * 0.5)
        adjusted_pct = round(adjusted * 100, 1)

        if adjusted_pct >= 70:
            verdict = 'BANJIR'
        elif adjusted_pct >= 40:
            verdict = 'BANJIR RINGAN'
        elif adjusted_pct >= 20:
            verdict = 'HANYA GENANGAN'
        else:
            verdict = 'AMAN'

        return adjusted_pct, verdict, round(precision * 100, 1)

    except Exception:
        return yolo_conf * 100, 'UNKNOWN', 50.0

'''

with open('apps/dashboard/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Insert after imports section, before is_water_region
insert_after = "from apps.notifications.models import Notification\n\n"
if insert_after in content:
    content = content.replace(insert_after, insert_after + new_engine, 1)
    print("OK: DB Accuracy Engine inserted")
else:
    print("ERROR: insertion point not found")

with open('apps/dashboard/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Step 1 complete")
