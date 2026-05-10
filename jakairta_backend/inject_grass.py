"""
Sisipkan Grass Reference Zone Detector ke analyze_sim di views.py.

Cara kerja:
1. Ambil frame paling awal dari video (5% durasi) → "frame referensi"
2. Cari area rumput (HSV hijau) di frame referensi → zona patokan
3. Di frame analisis, periksa apakah zona itu masih hijau atau sudah jadi air
4. Jika rumput tenggelam → override status menjadi BANJIR
"""

GRASS_DETECTOR_CODE = '''
        # ═══════════════════════════════════════════════════════════
        #  GRASS REFERENCE ZONE DETECTOR
        #  Deteksi banjir berdasarkan tenggelamnya rumput patokan
        # ═══════════════════════════════════════════════════════════
        grass_status = _analyze_grass_zone(stream_url, frame, width, height)
        grass_submerged   = grass_status['submerged']
        grass_zone        = grass_status['zone']       # {'x','y','w','h'} persen frame
        grass_green_pct   = grass_status['green_pct']
        grass_water_pct   = grass_status['water_pct']
        grass_found       = grass_status['grass_found']
        # ═══════════════════════════════════════════════════════════
'''

GRASS_FUNCTION_CODE = '''
# ══════════════════════════════════════════════════════════════
#  HELPER: Grass Reference Zone Detector
# ══════════════════════════════════════════════════════════════

def _analyze_grass_zone(video_path, current_frame, width, height):
    """
    Ambil frame awal video → cari zona rumput (hijau) → 
    periksa apakah zona itu kini berisi air di frame saat ini.

    Returns dict:
        submerged   : bool  — apakah rumput tenggelam?
        zone        : dict  — {x,y,w,h} dalam % frame
        green_pct   : float — % piksel hijau di zona referensi
        water_pct   : float — % piksel air di zona referensi saat ini
        grass_found : bool  — apakah rumput ditemukan di frame awal?
    """
    import cv2
    import numpy as np

    result = {
        'submerged': False,
        'zone': None,
        'green_pct': 0.0,
        'water_pct': 0.0,
        'grass_found': False,
    }

    try:
        # ── 1. Ambil frame referensi (5% durasi = sebelum banjir) ──
        cap_ref = cv2.VideoCapture(video_path)
        if not cap_ref.isOpened():
            return result

        total_frames = int(cap_ref.get(cv2.CAP_PROP_FRAME_COUNT))
        ref_pos = max(0, int(total_frames * 0.05))  # 5% awal video
        cap_ref.set(cv2.CAP_PROP_POS_FRAMES, ref_pos)
        ok_ref, ref_frame = cap_ref.read()
        cap_ref.release()

        if not ok_ref:
            return result

        h, w = ref_frame.shape[:2]
        hsv_ref = cv2.cvtColor(ref_frame, cv2.COLOR_BGR2HSV)

        # ── 2. Cari area rumput/hijau di frame referensi ──
        # HSV range rumput: hijau muda - hijau tua
        mask_grass = cv2.inRange(hsv_ref, np.array([35, 40, 40]), np.array([85, 255, 220]))

        # Morphology untuk bersihkan noise
        kernel = np.ones((7, 7), np.uint8)
        mask_grass = cv2.morphologyEx(mask_grass, cv2.MORPH_CLOSE, kernel)
        mask_grass = cv2.morphologyEx(mask_grass, cv2.MORPH_OPEN, kernel)

        # ── 3. Temukan kontur terbesar (zona rumput utama) ──
        contours, _ = cv2.findContours(mask_grass, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            result['grass_found'] = False
            return result

        # Ambil kontur terbesar
        largest = max(contours, key=cv2.contourArea)
        area_px = cv2.contourArea(largest)

        # Minimal 2% frame agar dianggap zona rumput valid
        if area_px < (h * w * 0.02):
            result['grass_found'] = False
            return result

        gx, gy, gw, gh = cv2.boundingRect(largest)
        result['grass_found'] = True
        result['zone'] = {
            'x': round((gx / w) * 100, 1),
            'y': round((gy / h) * 100, 1),
            'w': round((gw / w) * 100, 1),
            'h': round((gh / h) * 100, 1),
            'px': {'x': gx, 'y': gy, 'w': gw, 'h': gh},
        }

        # Hitung % hijau di zona referensi
        zone_ref = mask_grass[gy:gy+gh, gx:gx+gw]
        zone_total_px = gw * gh
        green_pixels = int(cv2.countNonZero(zone_ref))
        result['green_pct'] = round((green_pixels / zone_total_px) * 100, 1) if zone_total_px > 0 else 0.0

        # ── 4. Periksa zona yang sama di frame saat ini ──
        hsv_cur = cv2.cvtColor(current_frame, cv2.COLOR_BGR2HSV)
        cur_zone = hsv_cur[gy:gy+gh, gx:gx+gw]

        # Cek warna air/banjir di zona yang sama
        # Coklat keruh (lumpur), abu cerah, biru keruh
        mask_water_cur  = cv2.inRange(cur_zone, np.array([5,  35, 60]),  np.array([30, 255, 220]))
        mask_water_cur |= cv2.inRange(cur_zone, np.array([85, 25, 50]),  np.array([130,220, 200]))
        mask_water_cur |= cv2.inRange(cur_zone, np.array([15, 25, 80]),  np.array([35, 210, 220]))
        # Abu cerah (aspal basah / permukaan air siang)
        mask_water_cur |= cv2.inRange(cur_zone, np.array([0,  0,  130]), np.array([180, 40, 220]))

        # Cek sisa hijau di zona saat ini
        mask_green_cur = cv2.inRange(cur_zone, np.array([35, 40, 40]), np.array([85, 255, 220]))

        water_px_cur = int(cv2.countNonZero(mask_water_cur))
        green_px_cur = int(cv2.countNonZero(mask_green_cur))

        result['water_pct']  = round((water_px_cur / zone_total_px) * 100, 1) if zone_total_px > 0 else 0.0
        cur_green_pct        = round((green_px_cur / zone_total_px) * 100, 1) if zone_total_px > 0 else 0.0

        # ── 5. Tentukan apakah rumput tenggelam ──
        # Tenggelam jika:
        #   - Warna air > 30% di zona rumput, ATAU
        #   - Hijau tersisa < 20% dari semula (rumput hilang)
        green_loss_ratio = 1.0 - (cur_green_pct / result['green_pct']) if result['green_pct'] > 0 else 0.0
        result['submerged'] = (result['water_pct'] > 30.0) or (green_loss_ratio > 0.70)

        return result

    except Exception as e:
        result['error'] = str(e)
        return result

'''

with open('apps/dashboard/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Insert helper function before analyze_sim
insert_before = "@login_required(login_url='/dashboard/login/')\n@require_POST\ndef analyze_sim(request, sim_id):"
if insert_before in content:
    content = content.replace(insert_before, GRASS_FUNCTION_CODE + insert_before, 1)
    print("OK: _analyze_grass_zone function inserted")
else:
    print("ERROR: analyze_sim not found")

# 2. Insert grass detector call right after frame is captured in analyze_sim
# Find the line after: height, width = frame.shape[:2]
# followed by: # --- Kecerahan frame + DB calibration ---
old_brightness_block = (
    "        height, width = frame.shape[:2]\n"
    "\n"
    "        # --- Kecerahan frame + DB calibration ---\n"
    "        import cv2 as _cv2s\n"
)
new_brightness_block = (
    "        height, width = frame.shape[:2]\n"
    "\n"
    "        # --- Kecerahan frame + DB calibration ---\n"
    "        import cv2 as _cv2s\n"
)

# We need to insert GRASS_DETECTOR_CODE right before the YOLO run.
# It should go after the sim_yolo_conf/sim_hsv_min block and before: results = model(frame, ...)
old_model_call = "        results = model(frame, verbose=False, conf=sim_yolo_conf)\n"
new_model_call = GRASS_DETECTOR_CODE + "        results = model(frame, verbose=False, conf=sim_yolo_conf)\n"

if old_model_call in content:
    content = content.replace(old_model_call, new_model_call, 1)
    print("OK: Grass detector call inserted before model inference")
else:
    print("WARN: model call pattern not found")

with open('apps/dashboard/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Step 1 complete")
