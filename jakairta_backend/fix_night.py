"""
Fix two things in views.py:
1. Add night frame detection for CCTV (raise threshold when dark)
2. Pass hsv_min_water to is_water_region calls
"""
import re

with open('apps/dashboard/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ── Fix 1: Add night detection after frame capture in analyze_camera ──
old_camera = (
        "        height, width = frame.shape[:2]\n"
        "        results = model(frame, verbose=False, conf=max(adaptive_conf, 0.60))\n"
        "\n"
        "        # --- VEHICLE FILTER (Mencegah false positive motor/mobil terdeteksi sebagai air) ---\n"
        "        vehicle_boxes = []\n"
)
new_camera = (
        "        height, width = frame.shape[:2]\n"
        "\n"
        "        # --- Deteksi frame malam → threshold lebih ketat ---\n"
        "        import cv2 as _cv2n; import numpy as _np\n"
        "        _gray = _cv2n.cvtColor(frame, _cv2n.COLOR_BGR2GRAY)\n"
        "        mean_brightness = float(_gray.mean())\n"
        "        is_night = mean_brightness < 75\n"
        "        hsv_min_water = 0.55 if is_night else 0.40\n"
        "        yolo_conf = max(adaptive_conf, 0.72) if is_night else max(adaptive_conf, 0.62)\n"
        "        # -------------------------------------------------------\n"
        "\n"
        "        results = model(frame, verbose=False, conf=yolo_conf)\n"
        "\n"
        "        # --- VEHICLE FILTER ---\n"
        "        vehicle_boxes = []\n"
)

if old_camera in content:
    content = content.replace(old_camera, new_camera, 1)
    print("OK: Night detection added to analyze_camera")
else:
    print("WARN: analyze_camera pattern not found")

# ── Fix 2: Update is_water_region calls in analyze_camera to use hsv_min_water ──
content = content.replace(
    "if cls_name in ['water', 'flood'] and not is_water_region(frame, x1, y1, x2, y2):\n"
    "                    continue  # Abaikan — bukan air, mungkin motor/aspal!\n"
    "                # --------------------------------------\n"
    "\n"
    "                detections.append({\n"
    "                    'class': cls_name, \n"
    "                    'confidence': round(conf * 100, 1),\n"
    "                    'box': {\n"
    "                        'x': round((x1 / width) * 100, 2),\n"
    "                        'y': round((y1 / height) * 100, 2),\n"
    "                        'w': round(((x2 - x1) / width) * 100, 2),\n"
    "                        'h': round(((y2 - y1) / height) * 100, 2)\n"
    "                    }\n"
    "                })\n"
    "                \n"
    "                if masks is None and cls_name == 'water':",
    "if cls_name in ['water', 'flood'] and not is_water_region(frame, x1, y1, x2, y2, min_water_ratio=hsv_min_water):\n"
    "                    continue  # Abaikan — bukan air!\n"
    "                # --------------------------------------\n"
    "\n"
    "                detections.append({\n"
    "                    'class': cls_name,\n"
    "                    'confidence': round(conf * 100, 1),\n"
    "                    'box': {\n"
    "                        'x': round((x1 / width) * 100, 2),\n"
    "                        'y': round((y1 / height) * 100, 2),\n"
    "                        'w': round(((x2 - x1) / width) * 100, 2),\n"
    "                        'h': round(((y2 - y1) / height) * 100, 2)\n"
    "                    }\n"
    "                })\n"
    "\n"
    "                if masks is None and cls_name == 'water':",
    1
)
print("OK: hsv_min_water passed to analyze_camera water check")

with open('apps/dashboard/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: views.py updated")
