from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
import json

from apps.areas.models import Area, FloodStatus
from apps.cctv.models import CCTVCamera
from apps.weather.models import WeatherForecast, WeatherData
from apps.notifications.models import Notification



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


def is_water_region(frame, x1, y1, x2, y2, min_water_ratio=0.40):
    """
    Validasi KETAT apakah region bounding box benar-benar berisi air banjir.

    Warna air banjir NYATA:
      - Coklat keruh (lumpur, air tanah) dengan SATURATION tinggi
      - Biru-hijau keruh (sungai) dengan tekstur reflektif
    
    Bukan air (DITOLAK):
      - Hitam pekat -> aspal, motor, ban
      - Abu-abu gelap -> aspal kering/basah malam hari
      - Apapun dengan kecerahan rata-rata sangat rendah (<60/255)
    """
    try:
        import cv2
        import numpy as np
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            return False

        roi = frame[y1:y2, x1:x2]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        total_pixels = roi.shape[0] * roi.shape[1]
        if total_pixels == 0:
            return False

        # --- Cek kecerahan rata-rata (V channel) ---
        mean_brightness = float(hsv[:, :, 2].mean())
        # Jika rata-rata region sangat gelap (<60), itu aspal/motor malam hari, bukan air
        if mean_brightness < 60:
            return False

        # --- Warna AIR BANJIR NYATA (kriteria lebih ketat) ---
        # Coklat/tan keruh (lumpur, air tanah) — SATURATION tinggi (>40)
        mask_brown = cv2.inRange(hsv, np.array([5, 40, 70]), np.array([25, 255, 230]))
        # Biru-hijau keruh (sungai/kanal) — SATURATION cukup (>30)
        mask_blue  = cv2.inRange(hsv, np.array([85, 30, 60]), np.array([130, 220, 210]))
        # Tan/kuning keruh (banjir Jakarta yang biasanya coklat kekuningan)
        mask_tan   = cv2.inRange(hsv, np.array([15, 30, 80]), np.array([35, 200, 220]))
        # Putih berkilau DENGAN kecerahan sangat tinggi (pantulan air di siang hari)
        mask_white = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 30, 255]))

        # --- Yang BUKAN air ---
        # Hitam/gelap (aspal, motor, ban) — nilai <80
        mask_dark = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 80]))
        # Abu-abu aspal (saturation sangat rendah, nilai medium) — sering salah deteksi
        mask_asphalt = cv2.inRange(hsv, np.array([0, 0, 80]), np.array([180, 25, 180]))

        water_pixels = int(
            cv2.countNonZero(mask_brown) +
            cv2.countNonZero(mask_blue) +
            cv2.countNonZero(mask_tan) +
            cv2.countNonZero(mask_white)
        )
        dark_pixels = int(cv2.countNonZero(mask_dark))
        asphalt_pixels = int(cv2.countNonZero(mask_asphalt))

        water_ratio = water_pixels / total_pixels
        dark_ratio = dark_pixels / total_pixels
        asphalt_ratio = asphalt_pixels / total_pixels

        # Tolak jika didominasi gelap (aspal/motor)
        if dark_ratio > 0.35:
            return False
        # Tolak jika didominasi abu-abu aspal tanpa warna air cukup
        if asphalt_ratio > 0.50 and water_ratio < 0.20:
            return False
        # Terima hanya jika benar-benar ada warna air banjir
        return water_ratio >= min_water_ratio
    except Exception:
        return False  # Jika error, tolak (aman dari false positive)

# ─── Auth ─────────────────────────────────────────────────────────────────────

def dashboard_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    error = None
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect('dashboard_home')
        error = "Email atau password salah, atau akun tidak memiliki akses staff."
    return render(request, 'dashboard/login.html', {'error': error})


def dashboard_logout(request):
    logout(request)
    return redirect('dashboard_login')


# ─── Home ─────────────────────────────────────────────────────────────────────

@login_required(login_url='/dashboard/login/')
def dashboard_home(request):
    from apps.areas.models import Area, FloodStatus
    from apps.cctv.models import CCTVCamera, VideoSimulasi
    from apps.weather.models import WeatherData
    from apps.notifications.models import Notification

    areas = Area.objects.filter(is_active=True).order_by('district', 'name')
    areas_data = []
    for area in areas:
        cam = area.cameras.filter(is_active=True).first()
        sim = area.simulations.filter(is_active=True).first()
        latest_weather = area.weather_data.order_by('-recorded_at').first()
        rain_mm = latest_weather.rainfall if latest_weather else 0.0
        weather_met = rain_mm >= 10.0
        cctv_met = cam and cam.detection_result == CCTVCamera.DetectionResult.FLOOD
        both_met = weather_met and cctv_met
        areas_data.append({
            'area': area,
            'cam_id': cam.id if cam else None,
            'cam_url': cam.stream_url if cam else '',
            'sim_id': sim.id if sim else None,
            'sim_url': sim.video_file.url if sim and sim.video_file else '',
            'rain_mm': rain_mm,
            'weather_met': weather_met,
            'cctv_met': cctv_met,
            'both_met': both_met,
        })

    stats = {
        'total_areas': areas.count(),
        'flood_areas': areas.filter(status=FloodStatus.BANJIR).count(),
        'warning_areas': areas.filter(status=FloodStatus.POTENSIAL).count(),
        'safe_areas': areas.filter(status=FloodStatus.AMAN).count(),
    }
    return render(request, 'dashboard/home.html', {
        'areas_data': areas_data,
        'stats': stats,
        'user': request.user,
    })


# ─── Send Alert ───────────────────────────────────────────────────────────────

@login_required(login_url='/dashboard/login/')
@require_POST
def send_alert(request, area_id):
    from apps.areas.models import Area
    from apps.notifications.models import Notification
    area = Area.objects.filter(id=area_id).first()
    if not area:
        return JsonResponse({'success': False, 'message': 'Wilayah tidak ditemukan.'}, status=404)
    force = request.POST.get('force') == 'true'
    try:
        Notification.objects.create(
            area=area,
            message=f"⚠️ PERINGATAN BANJIR — {area.name}, {area.district}. Segera ambil tindakan pencegahan.",
            is_sent=True,
            sent_at=timezone.now(),
        )
        return JsonResponse({'success': True, 'message': f'Peringatan berhasil dikirim untuk {area.name}.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# ─── ARIMA Predict ────────────────────────────────────────────────────────────

# Titik-titik pantauan Jakarta untuk prediksi cuaca akurat
JAKARTA_MONITOR_POINTS = [
    {'name': 'Monas',  'lat': -6.1754, 'lon': 106.8272},
    {'name': 'Gambir', 'lat': -6.1784, 'lon': 106.8316},
]


def _fetch_and_save_weather(point: dict) -> dict | None:
    """
    Fetch cuaca real-time dari OpenWeatherMap untuk satu titik, simpan ke DB,
    dan kembalikan data parsed. Tidak melempar exception.
    """
    try:
        from apps.weather.services import OpenWeatherService
        from apps.weather.models import WeatherData

        raw = OpenWeatherService.fetch_current(lat=point['lat'], lon=point['lon'])
        if not raw:
            return None

        parsed = OpenWeatherService.parse_current(raw)
        if not parsed:
            return None

        # Simpan ke WeatherData (upsert berdasarkan menit ini)
        from django.utils import timezone as tz
        from datetime import timedelta
        now = tz.now().replace(second=0, microsecond=0)
        WeatherData.objects.update_or_create(
            source=WeatherData.Source.OPENWEATHER,
            recorded_at=now,
            defaults={
                'temperature': parsed.get('temperature'),
                'humidity':    parsed.get('humidity'),
                'rainfall':    parsed.get('rainfall', 0.0),
                'wind_speed':  parsed.get('wind_speed'),
                'description': f"[{point['name']}] {parsed.get('description', '')}",
                'weather_code': parsed.get('weather_code', ''),
                'raw_data':    raw,
            }
        )
        parsed['point'] = point['name']
        return parsed
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"fetch_and_save_weather({point['name']}) gagal: {e}")
        return None


@login_required(login_url='/dashboard/login/')
@require_POST
def predict_flood(request):
    try:
        import pandas as pd
        import numpy as np
        from apps.weather.models import WeatherData, WeatherForecast
        from django.utils import timezone as tz
        from datetime import timedelta

        now = tz.now()

        # ── 1. Fetch real-time cuaca dari Monas & Gambir ──────────────────────
        live_points = []
        fetch_errors = []
        for point in JAKARTA_MONITOR_POINTS:
            result = _fetch_and_save_weather(point)
            if result:
                live_points.append(result)
            else:
                fetch_errors.append(point['name'])

        live_info = (
            f"📡 Data live: {', '.join(p['point'] for p in live_points)}"
            if live_points else
            "⚠️ Fetch real-time gagal — menggunakan data historis DB"
        )

        # ── 2. Ambil data historis untuk ARIMA (72 jam → 30 hari → semua → baseline) ──
        qs = None
        window_label = ''
        use_baseline = False
        for hours, label in [(72, '72 jam terakhir'), (24 * 30, '30 hari'), (None, 'semua data DB')]:
            candidate = (
                WeatherData.objects.filter(recorded_at__gte=now - timedelta(hours=hours))
                if hours else WeatherData.objects.all()
            ).order_by('recorded_at')
            if candidate.count() >= 5:
                qs = candidate
                window_label = label
                break

        if qs is None or qs.count() < 5:
            # Baseline Jakarta: pola realistis 24 jam (pagi kering, siang-sore hujan)
            import random
            random.seed(42)
            rainfall_raw  = [0.0, 0.0, 0.2, 0.5, 1.0, 2.5, 5.0, 8.0, 12.0, 15.0,
                             10.0, 6.0, 3.0, 1.5, 0.5, 0.0, 0.0, 0.0, 0.5, 2.0,
                             5.5, 8.0, 11.0, 7.0, 4.0, 2.0, 0.8, 0.2, 0.0, 0.0,
                             0.3, 1.2, 4.5, 9.0, 13.0, 10.0, 6.5, 3.5, 1.0, 0.2,
                             0.0, 0.0, 0.0, 0.3, 1.5, 5.0, 7.5, 9.5]
            temps_raw     = [26.5, 26.0, 25.8, 26.0, 27.0, 28.5, 30.0, 31.5, 32.0, 31.5,
                             31.0, 30.5, 30.0, 31.0, 32.0, 32.5, 31.5, 30.0, 28.5, 27.5,
                             27.0, 26.5, 26.0, 25.8, 25.5, 25.8, 26.0, 27.0, 28.5, 30.0,
                             31.5, 32.0, 31.0, 30.0, 29.0, 28.0, 27.5, 27.0, 26.5, 26.0,
                             25.8, 25.5, 25.8, 26.2, 27.5, 29.0, 30.5, 31.0]
            humids_raw    = [88, 90, 91, 90, 87, 82, 75, 68, 65, 66,
                             68, 70, 72, 70, 66, 63, 65, 68, 75, 80,
                             85, 87, 89, 90, 91, 90, 88, 83, 78, 72,
                             67, 64, 65, 68, 72, 76, 80, 84, 87, 89,
                             91, 92, 90, 88, 83, 77, 71, 67]
            use_baseline = True
            window_label = 'baseline pola Jakarta (data DB kosong)'
        else:
            data_qs = list(qs)
            rainfall_raw = [float(d.rainfall or 0.0) for d in data_qs]
            temps_raw    = [float(d.temperature) for d in data_qs if d.temperature is not None]
            humids_raw   = [float(d.humidity) for d in data_qs if d.humidity is not None]

            # Pad jika ada data humidity/temp yang kurang
            if not humids_raw:
                humids_raw = [80.0] * len(rainfall_raw)
            if not temps_raw:
                temps_raw = [29.0] * len(rainfall_raw)

            # Sejajarkan panjang semua series
            min_len = min(len(rainfall_raw), len(temps_raw), len(humids_raw))
            rainfall_raw = rainfall_raw[:min_len]
            temps_raw    = temps_raw[:min_len]
            humids_raw   = humids_raw[:min_len]

        # ── 3. Jalankan ARIMA Triple-Fit (Suhu + Kelembapan + Curah Hujan) ─────
        try:
            from pmdarima import auto_arima as _auto_arima
            from statsmodels.tsa.arima.model import ARIMA as _ARIMA

            s_rain = pd.Series(rainfall_raw, dtype=float).fillna(0)
            s_temp = pd.Series(temps_raw, dtype=float).fillna(29.0)
            s_hum  = pd.Series(humids_raw, dtype=float).fillna(80.0)

            def _fit_predict(series, n=5):
                """Fit auto_arima, fallback ke ARIMA(1,0,0), fallback ke mean."""
                try:
                    if len(series) >= 10:
                        m = _auto_arima(series, seasonal=False, suppress_warnings=True,
                                        error_action='ignore', max_p=3, max_q=2, d=0)
                        return m.predict(n_periods=n)
                    else:
                        m = _ARIMA(series, order=(1, 0, 0)).fit()
                        return m.forecast(steps=n)
                except Exception:
                    return [float(series.mean())] * n

            rain_forecast = _fit_predict(s_rain)
            temp_forecast = _fit_predict(s_temp)
            hum_forecast  = _fit_predict(s_hum)

        except ImportError:
            # Fallback murni jika library tidak tersedia
            rain_forecast = [float(np.mean(rainfall_raw))] * 5
            temp_forecast = [float(np.mean(temps_raw))] * 5
            hum_forecast  = [float(np.mean(humids_raw))] * 5

        # ── 4. Koreksi dengan data live (jika berhasil) ────────────────────────
        # Rata-rata curah hujan live menjadi "anchor" untuk jam pertama
        if live_points:
            live_rain_avg = float(np.mean([p.get('rainfall', 0.0) for p in live_points]))
            live_temp_avg = float(np.mean([p.get('temperature', 29.0) for p in live_points]))
            live_hum_avg  = float(np.mean([p.get('humidity', 80.0) for p in live_points]))
            # Blending: jam 1 = 70% live + 30% ARIMA, jam berikutnya penuh ARIMA
            rain_forecast = list(rain_forecast)
            temp_forecast = list(temp_forecast)
            hum_forecast  = list(hum_forecast)
            rain_forecast[0] = 0.7 * live_rain_avg + 0.3 * max(0, float(rain_forecast[0]))
            temp_forecast[0] = 0.7 * live_temp_avg + 0.3 * float(temp_forecast[0])
            hum_forecast[0]  = 0.7 * live_hum_avg  + 0.3 * float(hum_forecast[0])

        # ── 5. Simpan hasil ke WeatherForecast ────────────────────────────────
        try:
            for i in range(5):
                f_rain = max(0.0, float(rain_forecast[i]))
                f_temp = round(float(temp_forecast[i]), 1)
                f_hum  = round(float(hum_forecast[i]), 0)
                if f_rain >= 50:
                    desc = 'ARIMA: KRITIS (Hujan Sangat Lebat)'
                elif f_rain >= 20:
                    desc = 'ARIMA: SIAGA (Hujan Lebat)'
                elif f_rain >= 10:
                    desc = 'ARIMA: WASPADA (Hujan Sedang)'
                else:
                    desc = 'ARIMA: Aman'
                WeatherForecast.objects.update_or_create(
                    source='openweather_arima_ml',
                    forecast_time=now + timedelta(hours=i + 1),
                    defaults={
                        'temperature': f_temp,
                        'humidity':    int(f_hum),
                        'rainfall':    round(f_rain, 2),
                        'description': desc,
                        'rainfall_probability': min(100, int(f_rain * 3)),
                        'raw_data': {'monas_gambir_blend': True, 'live_points': len(live_points)},
                    }
                )
        except Exception:
            pass  # Simpan ke DB adalah bonus, tidak boleh crash prediksi

        # ── 6. Format hasil untuk dashboard ────────────────────────────────────
        results = []
        flood_risk = False
        for i in range(5):
            t    = now + timedelta(hours=i + 1)
            val  = max(0.0, float(rain_forecast[i]))
            temp = round(float(temp_forecast[i]), 1)
            hum  = round(float(hum_forecast[i]), 0)

            if val >= 50:
                risk, intensity = 'KRITIS', 'Sangat Lebat'
            elif val >= 20:
                risk, intensity = 'SIAGA', 'Lebat'
            elif val >= 10:
                risk, intensity = 'WASPADA', 'Sedang'
            elif val >= 2:
                risk, intensity = 'WASPADA', 'Gerimis'
            else:
                risk, intensity = 'AMAN', 'Tidak Hujan'

            if risk in ('KRITIS', 'SIAGA'):
                flood_risk = True

            results.append({
                'date':        t.strftime('%d/%m'),
                'time':        t.strftime('%H:%M'),
                'rainfall':    round(val, 1),
                'intensity':   intensity,
                'temperature': temp,
                'humidity':    int(hum),
                'risk':        risk,
            })

        live_label = f"📍 {', '.join(p['point'] for p in live_points)}" if live_points else "📂 historis DB"
        src_note   = f" | Titik: {live_label} | Basis: {window_label}"
        summary = (
            f"🚨 RISIKO BANJIR TINGGI — Curah hujan lebat diprediksi dalam 5 jam ke depan!{src_note}"
            if flood_risk else
            f"✅ Kondisi Aman — Curah hujan dalam batas normal.{src_note}"
        )

        return JsonResponse({
            'success':    True,
            'flood_risk': flood_risk,
            'summary':    summary,
            'forecasts':  results,
            'live_info':  live_info,
            'fetch_errors': fetch_errors,
        })

    except Exception as e:
        import traceback
        return JsonResponse({'success': False, 'message': str(e), 'detail': traceback.format_exc()})







# ─── YOLOv8 Analyze CCTV ─────────────────────────────────────────────────────

@login_required(login_url='/dashboard/login/')
@require_POST
def analyze_camera(request, camera_id):
    try:
        from apps.cctv.models import CCTVCamera, FloodAnalysisLog
        cam = CCTVCamera.objects.filter(id=camera_id).first()
        if not cam:
            return JsonResponse({'success': False, 'message': 'Kamera tidak ditemukan.'})
        if not cam.stream_url:
            return JsonResponse({'success': False, 'message': 'Kamera tidak memiliki URL stream.'})

        import cv2, numpy as np
        from ultralytics import YOLO
        import os
        from django.conf import settings

        model_path = os.path.join(settings.BASE_DIR, 'best.pt')
        if not os.path.exists(model_path):
            model_path = os.path.join(settings.BASE_DIR, '..', 'yolov8_flood_vision', 'best.pt')

        cap = cv2.VideoCapture(cam.stream_url)
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            return JsonResponse({'success': False, 'message': 'Gagal mengambil frame dari stream.'})

        model = YOLO(model_path)
        results = model(frame, conf=0.5)
        detections = []
        h, w = frame.shape[:2]
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_name = model.names[int(box.cls[0])]
                detections.append({
                    'class': cls_name,
                    'confidence': round(conf * 100, 1),
                    'box': {'x': round(x1/w*100,1), 'y': round(y1/h*100,1),
                            'w': round((x2-x1)/w*100,1), 'h': round((y2-y1)/h*100,1)},
                })

        has_water = any('flood' in d['class'].lower() or 'water' in d['class'].lower() for d in detections)
        water_ratio = sum(d['box']['w']*d['box']['h']/10000 for d in detections if 'flood' in d['class'].lower() or 'water' in d['class'].lower())
        is_flood = has_water and water_ratio > 5
        status = 'BANJIR' if is_flood else ('HANYA GENANGAN' if has_water else 'AMAN (TIDAK BANJIR)')
        risk = 'critical' if is_flood else ('caution' if has_water else 'safe')

        log = FloodAnalysisLog.objects.create(
            area=cam.area, camera=cam, source_type='cctv', source_name=cam.name,
            status_banjir=status.lower().replace(' ', '_')[:30],
            is_flood=is_flood, has_water=has_water,
            water_area_ratio=round(water_ratio, 1),
            risk_level=risk, total_objects_detected=len(detections),
            confidence_score=round(sum(d['confidence'] for d in detections)/max(len(detections),1), 1),
            water_level_text='Tinggi' if water_ratio > 20 else ('Sedang' if water_ratio > 5 else 'Rendah'),
            rain_intensity='Tidak diketahui',
            recommendation='Segera evakuasi!' if is_flood else 'Pantau terus kondisi.',
        )

        return JsonResponse({
            'success': True, 'status_banjir': status, 'is_flood': is_flood,
            'has_water': has_water, 'water_area_ratio': round(water_ratio, 1),
            'risk_level': risk, 'total_objects': len(detections),
            'detections': detections, 'water_level_text': log.water_level_text,
            'rain_intensity': log.rain_intensity, 'recommendation': log.recommendation,
            'analyzed_at': log.analyzed_at.strftime('%H:%M:%S'),
            'grass_reference': None,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# ─── YOLOv8 Analyze Simulasi ──────────────────────────────────────────────────

@login_required(login_url='/dashboard/login/')
@require_POST
def analyze_sim(request, sim_id):
    try:
        from apps.cctv.models import VideoSimulasi, FloodAnalysisLog
        sim = VideoSimulasi.objects.filter(id=sim_id).first()
        if not sim:
            return JsonResponse({'success': False, 'message': 'Simulasi tidak ditemukan.'})
        if not sim.video_file:
            return JsonResponse({'success': False, 'message': 'File video tidak tersedia.'})

        import cv2, numpy as np, os
        from ultralytics import YOLO
        from django.conf import settings

        model_path = os.path.join(settings.BASE_DIR, 'best.pt')
        if not os.path.exists(model_path):
            model_path = os.path.join(settings.BASE_DIR, '..', 'yolov8_flood_vision', 'best.pt')

        video_path = os.path.join(settings.MEDIA_ROOT, sim.video_file.name)
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(30, total_frames // 2))
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            return JsonResponse({'success': False, 'message': 'Gagal membaca frame video.'})

        model = YOLO(model_path)
        results = model(frame, conf=0.45)
        detections = []
        h, w = frame.shape[:2]
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_name = model.names[int(box.cls[0])]
                detections.append({
                    'class': cls_name,
                    'confidence': round(conf * 100, 1),
                    'box': {'x': round(x1/w*100,1), 'y': round(y1/h*100,1),
                            'w': round((x2-x1)/w*100,1), 'h': round((y2-y1)/h*100,1)},
                })

        has_water = any('flood' in d['class'].lower() or 'water' in d['class'].lower() for d in detections)
        water_ratio = sum(d['box']['w']*d['box']['h']/10000 for d in detections if 'flood' in d['class'].lower() or 'water' in d['class'].lower())
        is_flood = has_water and water_ratio > 5
        status = 'BANJIR' if is_flood else ('HANYA GENANGAN' if has_water else 'AMAN (TIDAK BANJIR)')
        risk = 'critical' if is_flood else ('caution' if has_water else 'safe')

        log = FloodAnalysisLog.objects.create(
            area=sim.area, source_type='simulation', source_name=sim.title,
            status_banjir=status.lower().replace(' ', '_')[:30],
            is_flood=is_flood, has_water=has_water,
            water_area_ratio=round(water_ratio, 1),
            risk_level=risk, total_objects_detected=len(detections),
            confidence_score=round(sum(d['confidence'] for d in detections)/max(len(detections),1), 1),
            water_level_text='Tinggi' if water_ratio > 20 else ('Sedang' if water_ratio > 5 else 'Rendah'),
            rain_intensity='Tidak diketahui',
            recommendation='Segera evakuasi!' if is_flood else 'Pantau terus kondisi.',
        )

        return JsonResponse({
            'success': True, 'status_banjir': status, 'is_flood': is_flood,
            'has_water': has_water, 'water_area_ratio': round(water_ratio, 1),
            'risk_level': risk, 'total_objects': len(detections),
            'detections': detections, 'water_level_text': log.water_level_text,
            'rain_intensity': log.rain_intensity, 'recommendation': log.recommendation,
            'analyzed_at': log.analyzed_at.strftime('%H:%M:%S'),
            'grass_reference': None,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# ─── API Status ───────────────────────────────────────────────────────────────

@login_required(login_url='/dashboard/login/')
def api_status(request):
    from apps.areas.models import Area, FloodStatus
    from apps.cctv.models import CCTVCamera
    return JsonResponse({
        'total_areas': Area.objects.filter(is_active=True).count(),
        'flood_areas': Area.objects.filter(status=FloodStatus.BANJIR).count(),
        'active_cameras': CCTVCamera.objects.filter(is_active=True).count(),
        'timestamp': timezone.now().isoformat(),
    })


# ─── CRUD Wilayah ─────────────────────────────────────────────────────────────

@login_required(login_url='/dashboard/login/')
def area_add(request):
    from apps.areas.models import Area
    from apps.cctv.models import CCTVCamera
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        district = request.POST.get('district', '').strip()
        if not name or not district:
            return JsonResponse({'success': False, 'message': 'Nama dan kota wajib diisi.'})
        area = Area.objects.create(
            name=name, district=district,
            latitude=request.POST.get('latitude', -6.2),
            longitude=request.POST.get('longitude', 106.816),
        )
        cctv_url = request.POST.get('cctv_url', '').strip()
        if cctv_url:
            CCTVCamera.objects.create(name=f"CCTV {name}", area=area, stream_url=cctv_url, is_active=True)
        return JsonResponse({'success': True, 'message': f'Wilayah "{name}" berhasil ditambahkan.'})
    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@login_required(login_url='/dashboard/login/')
def area_edit(request, area_id):
    from apps.areas.models import Area
    from apps.cctv.models import CCTVCamera
    area = Area.objects.filter(id=area_id).first()
    if not area:
        return JsonResponse({'success': False, 'message': 'Wilayah tidak ditemukan.'}, status=404)
    cam = area.cameras.filter(is_active=True).first()
    cctv_url = cam.stream_url if cam else ''
    if request.method == 'GET':
        return JsonResponse({'id': area.id, 'name': area.name, 'district': area.district,
                             'latitude': float(area.latitude), 'longitude': float(area.longitude),
                             'cctv_url': cctv_url})
    if request.method == 'POST':
        area.name = request.POST.get('name', area.name).strip()
        area.district = request.POST.get('district', area.district).strip()
        area.latitude = request.POST.get('latitude', area.latitude)
        area.longitude = request.POST.get('longitude', area.longitude)
        area.save()
        new_cctv_url = request.POST.get('cctv_url', '').strip()
        if new_cctv_url:
            if cam:
                cam.stream_url = new_cctv_url; cam.save()
            else:
                CCTVCamera.objects.create(name=f"CCTV {area.name}", area=area, stream_url=new_cctv_url, is_active=True)
        elif cam and not new_cctv_url:
            cam.is_active = False; cam.save()
        return JsonResponse({'success': True, 'message': 'Wilayah berhasil diupdate.'})
    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@login_required(login_url='/dashboard/login/')
@require_POST
def area_delete(request, area_id):
    from apps.areas.models import Area
    area = Area.objects.filter(id=area_id).first()
    if not area:
        return JsonResponse({'success': False, 'message': 'Wilayah tidak ditemukan.'}, status=404)
    area.is_active = False
    area.save()
    return JsonResponse({'success': True, 'message': 'Wilayah berhasil dihapus.'})


# ─── CRUD Kamera CCTV ─────────────────────────────────────────────────────────

@login_required(login_url='/dashboard/login/')
def camera_add(request):
    from apps.cctv.models import CCTVCamera
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'message': 'Nama kamera wajib diisi.'})
        area_id = request.POST.get('area_id') or None
        cam = CCTVCamera.objects.create(
            name=name,
            area_id=area_id if area_id else None,
            stream_url=request.POST.get('stream_url', '').strip(),
            is_active=request.POST.get('is_active') == '1',
        )
        return JsonResponse({'success': True, 'message': f'Kamera "{name}" berhasil ditambahkan.', 'id': cam.id})
    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@login_required(login_url='/dashboard/login/')
def camera_edit(request, camera_id):
    from apps.cctv.models import CCTVCamera
    cam = CCTVCamera.objects.filter(id=camera_id).first()
    if not cam:
        return JsonResponse({'success': False, 'message': 'Kamera tidak ditemukan.'}, status=404)
    if request.method == 'GET':
        return JsonResponse({'id': cam.id, 'name': cam.name, 'area_id': cam.area_id,
                             'stream_url': cam.stream_url or '', 'is_active': cam.is_active})
    if request.method == 'POST':
        cam.name = request.POST.get('name', cam.name).strip()
        cam.area_id = request.POST.get('area_id') or None
        cam.stream_url = request.POST.get('stream_url', '').strip()
        cam.is_active = request.POST.get('is_active') == '1'
        cam.save()
        return JsonResponse({'success': True, 'message': 'Kamera berhasil diupdate.'})
    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@login_required(login_url='/dashboard/login/')
@require_POST
def camera_delete(request, camera_id):
    from apps.cctv.models import CCTVCamera
    cam = CCTVCamera.objects.filter(id=camera_id).first()
    if not cam:
        return JsonResponse({'success': False, 'message': 'Kamera tidak ditemukan.'}, status=404)
    cam.is_active = False
    cam.save()
    return JsonResponse({'success': True, 'message': 'Kamera berhasil dihapus.'})


# ─── CRUD Video Simulasi ──────────────────────────────────────────────────────

@login_required(login_url='/dashboard/login/')
def sim_add(request):
    from apps.cctv.models import VideoSimulasi
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            return JsonResponse({'success': False, 'message': 'Judul video wajib diisi.'})
        area_id = request.POST.get('area_id') or None
        sim = VideoSimulasi(
            title=title,
            area_id=area_id if area_id else None,
            is_active=request.POST.get('is_active') == '1',
        )
        if 'video_file' in request.FILES:
            sim.video_file = request.FILES['video_file']
        sim.save()
        return JsonResponse({'success': True, 'message': f'Video "{title}" berhasil diupload.', 'id': sim.id})
    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@login_required(login_url='/dashboard/login/')
def sim_edit(request, sim_id):
    from apps.cctv.models import VideoSimulasi
    sim = VideoSimulasi.objects.filter(id=sim_id).first()
    if not sim:
        return JsonResponse({'success': False, 'message': 'Simulasi tidak ditemukan.'}, status=404)
    if request.method == 'GET':
        return JsonResponse({'id': sim.id, 'title': sim.title, 'area_id': sim.area_id,
                             'video_file': sim.video_file.name if sim.video_file else '',
                             'is_active': sim.is_active})
    if request.method == 'POST':
        sim.title = request.POST.get('title', sim.title).strip()
        sim.area_id = request.POST.get('area_id') or None
        sim.is_active = request.POST.get('is_active') == '1'
        if 'video_file' in request.FILES:
            sim.video_file = request.FILES['video_file']
        sim.save()
        return JsonResponse({'success': True, 'message': 'Video simulasi berhasil diupdate.'})
    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@login_required(login_url='/dashboard/login/')
@require_POST
def sim_delete(request, sim_id):
    from apps.cctv.models import VideoSimulasi
    sim = VideoSimulasi.objects.filter(id=sim_id).first()
    if not sim:
        return JsonResponse({'success': False, 'message': 'Simulasi tidak ditemukan.'}, status=404)
    sim.is_active = False
    sim.save()
    return JsonResponse({'success': True, 'message': 'Video simulasi berhasil dihapus.'})
