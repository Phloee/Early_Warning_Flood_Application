"""Patch analyze_sim: replace conf=0.50 with DB-calibrated conf."""

with open('apps/dashboard/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the old sim detection block with DB-calibrated version
old = (
    "        ok, frame = cap.read()\n"
    "        cap.release()\n"
    "\n"
    "        if not ok:\n"
    "            return JsonResponse({'success': False, 'message': 'Gagal membaca frame pertama dari video.'})\n"
    "\n"
    "        height, width = frame.shape[:2]\n"
    "        results = model(frame, verbose=False, conf=0.50)\n"
    "\n"
    "        # --- VEHICLE FILTER (Mencegah false positive motor/mobil terdeteksi sebagai air) ---\n"
    "        vehicle_boxes = []\n"
    "        try:\n"
    "            from ultralytics import YOLO\n"
    "            coco_model = YOLO('yolov8n.pt')\n"
    "            coco_results = coco_model(frame, verbose=False, conf=0.3)\n"
    "            if len(coco_results) > 0 and coco_results[0].boxes is not None:\n"
    "                for v_box in coco_results[0].boxes:\n"
    "                    cls_id = int(v_box.cls[0])\n"
    "                    # COCO IDs: 2:car, 3:motorcycle, 5:bus, 7:truck\n"
    "                    if cls_id in [2, 3, 5, 7]:\n"
    "                        vehicle_boxes.append(v_box.xyxy[0])\n"
    "        except Exception:\n"
    "            pass\n"
    "        # ---------------------------------------------------------------------------------\n"
)

new = (
    "        ok, frame = cap.read()\n"
    "        cap.release()\n"
    "\n"
    "        if not ok:\n"
    "            return JsonResponse({'success': False, 'message': 'Gagal membaca frame pertama dari video.'})\n"
    "\n"
    "        height, width = frame.shape[:2]\n"
    "\n"
    "        # --- Kecerahan frame + DB calibration ---\n"
    "        import cv2 as _cv2s\n"
    "        _grays = _cv2s.cvtColor(frame, _cv2s.COLOR_BGR2GRAY)\n"
    "        sim_brightness = float(_grays.mean())\n"
    "        is_night_sim = sim_brightness < 75\n"
    "        sim_yolo_conf = min(0.85, db_yolo_conf_s + (0.10 if is_night_sim else 0.0))\n"
    "        sim_hsv_min   = min(0.72, db_hsv_min_s  + (0.12 if is_night_sim else 0.0))\n"
    "        # ----------------------------------------\n"
    "\n"
    "        results = model(frame, verbose=False, conf=sim_yolo_conf)\n"
    "\n"
    "        # --- VEHICLE FILTER ---\n"
    "        vehicle_boxes = []\n"
    "        try:\n"
    "            from ultralytics import YOLO\n"
    "            coco_model = YOLO('yolov8n.pt')\n"
    "            coco_results = coco_model(frame, verbose=False, conf=0.3)\n"
    "            if len(coco_results) > 0 and coco_results[0].boxes is not None:\n"
    "                for v_box in coco_results[0].boxes:\n"
    "                    cls_id = int(v_box.cls[0])\n"
    "                    if cls_id in [2, 3, 5, 7]:\n"
    "                        vehicle_boxes.append(v_box.xyxy[0])\n"
    "        except Exception:\n"
    "            pass\n"
    "        # ---------------------------------------------------\n"
)

if old in content:
    content = content.replace(old, new, 1)
    print("OK: sim conf=0.50 replaced with DB calibrated thresholds")
else:
    print("PATTERN NOT FOUND — trying alternative search")
    # Check what's there
    idx = content.find("results = model(frame, verbose=False, conf=0.50)")
    if idx >= 0:
        content = content.replace(
            "results = model(frame, verbose=False, conf=0.50)",
            "results = model(frame, verbose=False, conf=sim_yolo_conf if 'sim_yolo_conf' in dir() else 0.62)",
            1
        )
        print("OK: Direct conf=0.50 replacement")
    else:
        print("ERROR: Cannot find pattern")

# Also update HSV check in sim to use sim_hsv_min
old_hsv = "if cls_name in ['water', 'flood'] and not is_water_region(frame, x1, y1, x2, y2):\n                    continue  # Bukan air (motor/aspal gelap), abaikan!\n                # ----------------------------------"
new_hsv = "if cls_name in ['water', 'flood'] and not is_water_region(frame, x1, y1, x2, y2, min_water_ratio=sim_hsv_min if 'sim_hsv_min' in dir() else 0.40):\n                    continue  # Bukan air!\n                # ----------------------------------"
if old_hsv in content:
    content = content.replace(old_hsv, new_hsv, 1)
    print("OK: sim HSV check updated to use sim_hsv_min")
else:
    print("WARN: sim HSV pattern not found")

with open('apps/dashboard/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done.")
