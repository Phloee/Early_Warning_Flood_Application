"""
Perbaiki is_water_region agar jauh lebih ketat:
- Hapus abu-abu (aspal basah sering masuk kategori ini)
- Hanya terima coklat keruh NYATA dan biru keruh sungai
- Tolak jika area terlalu gelap (malam/aspal) = bukan air
- Tolak jika kendaraan > 30%
- Naikkan min_water_ratio default ke 0.40
- Naikkan confidence threshold YOLO ke 0.60
- Nonaktifkan fallback jika tidak ada air nyata
"""
import os

with open('apps/dashboard/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace is_water_region with stricter version
old_func = '''def is_water_region(frame, x1, y1, x2, y2, min_water_ratio=0.25):
    """
    Validasi apakah region bounding box benar-benar berisi air/genangan
    menggunakan analisis warna HSV.
    Air keruh/banjir biasanya berwarna: coklat, abu-abu, biru keruh, atau putih berkilau.
    Kendaraan biasanya berwarna: hitam pekat, atau saturasi sangat rendah dengan value sangat gelap.
    Returns True jika region terlihat seperti air.
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

        # --- Rentang warna AIR BANJIR (coklat keruh, abu-abu, biru keruh) ---
        # Coklat/oranye keruh (air tanah, lumpur)
        mask_brown = cv2.inRange(hsv, np.array([5, 20, 40]), np.array([30, 220, 220]))
        # Abu-abu (aspal basah, air jernih di bawah langit)
        mask_gray  = cv2.inRange(hsv, np.array([0, 0, 60]), np.array([180, 50, 200]))
        # Biru-hijau keruh (air sungai)
        mask_blue  = cv2.inRange(hsv, np.array([85, 15, 30]), np.array([130, 200, 200]))
        # Putih berkilau (pantulan cahaya di permukaan air)
        mask_white = cv2.inRange(hsv, np.array([0, 0, 180]), np.array([180, 40, 255]))

        # --- Hitam pekat = KENDARAAN, bukan air ---
        mask_vehicle_black = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 45]))

        water_pixels = int(cv2.countNonZero(mask_brown) + cv2.countNonZero(mask_gray) +
                           cv2.countNonZero(mask_blue) + cv2.countNonZero(mask_white))
        vehicle_pixels = int(cv2.countNonZero(mask_vehicle_black))

        water_ratio = water_pixels / total_pixels
        vehicle_ratio = vehicle_pixels / total_pixels

        # Tolak jika region didominasi warna hitam kendaraan (>50%)
        if vehicle_ratio > 0.50:
            return False
        # Terima jika setidaknya 25% piksel berwarna seperti air
        return water_ratio >= min_water_ratio
    except Exception:
        return True  # Jika gagal analisis, terima saja (fallback)'''

new_func = '''def is_water_region(frame, x1, y1, x2, y2, min_water_ratio=0.40):
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
        return False  # Jika error, tolak (aman dari false positive)'''

if old_func in content:
    content = content.replace(old_func, new_func, 1)
    print("OK: is_water_region replaced")
else:
    print("WARN: old_func not found exactly, trying partial...")
    # Try to find and replace by line range
    lines = content.split('\n')
    start_idx = None
    for i, line in enumerate(lines):
        if 'def is_water_region(' in line:
            start_idx = i
            break
    if start_idx is not None:
        # Find end of function (next def or empty line at indent 0)
        end_idx = start_idx + 1
        while end_idx < len(lines):
            if lines[end_idx].startswith('def ') or lines[end_idx].startswith('# ─'):
                break
            end_idx += 1
        lines[start_idx:end_idx] = new_func.split('\n')
        content = '\n'.join(lines)
        print(f"OK: Replaced lines {start_idx}-{end_idx}")
    else:
        print("ERROR: Function not found!")

# 2. Raise confidence threshold from 0.50 to 0.60
content = content.replace('conf=0.50) # Ditingkatkan ke 50% untuk mengurangi false positive', 'conf=0.60)')
content = content.replace("conf=adaptive_conf)", "conf=max(adaptive_conf, 0.60))")

# 3. Raise vehicle overlap IoU from 0.40 to 0.30 (lebih ketat)
content = content.replace('if box_area > 0 and (inter_area / box_area) > 0.4:', 
                          'if box_area > 0 and (inter_area / box_area) > 0.30:')

# 4. Also remove any remaining fallback "Force" lines
content = content.replace('water_area_ratio = 38.5 # Force Sangat Luas (Berbahaya)', '')

with open('apps/dashboard/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: All filters tightened")
print("Changes made:")
print("  - is_water_region: threshold 0.25 -> 0.40, reject dark/asphalt")
print("  - YOLO confidence: 0.50 -> 0.60 minimum")
print("  - Vehicle IoU: 0.40 -> 0.30 (stricter)")
print("  - Fallback: only triggers if HSV confirms real water")
