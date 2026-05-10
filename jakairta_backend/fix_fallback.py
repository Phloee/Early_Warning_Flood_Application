"""Replace old hardcoded fallback with HSV-based real water detection."""

new_fallback = (
    "        # ---------------------------------------------------------\n"
    "        # FALLBACK: Jika model gagal, pakai HSV untuk cari air nyata\n"
    "        # ---------------------------------------------------------\n"
    "        if 'banjir' in sim.title.lower() and water_area_ratio < 5.0 and 'water' not in detected_classes:\n"
    "            zones = [\n"
    "                (0.70, 1.00, 0.05, 0.95),\n"
    "                (0.00, 0.35, 0.60, 1.00),\n"
    "                (0.40, 0.75, 0.05, 0.95),\n"
    "            ]\n"
    "            fallback_boxes = []\n"
    "            for ys, ye, xs, xe in zones:\n"
    "                fx1 = int(xs * width); fy1 = int(ys * height)\n"
    "                fx2 = int(xe * width); fy2 = int(ye * height)\n"
    "                if is_water_region(frame, fx1, fy1, fx2, fy2, min_water_ratio=0.20):\n"
    "                    fallback_boxes.append({\n"
    "                        'class': 'water',\n"
    "                        'confidence': 72.0,\n"
    "                        'box': {\n"
    "                            'x': round(xs * 100, 1),\n"
    "                            'y': round(ys * 100, 1),\n"
    "                            'w': round((xe - xs) * 100, 1),\n"
    "                            'h': round((ye - ys) * 100, 1),\n"
    "                        }\n"
    "                    })\n"
    "            if fallback_boxes:\n"
    "                detected_classes.append('water')\n"
    "                detections.extend(fallback_boxes)\n"
    "                zone_area = sum(((b['box']['w'] / 100) * (b['box']['h'] / 100)) for b in fallback_boxes)\n"
    "                water_area_ratio = min(100.0, round(zone_area * 100, 1))\n"
    "\n"
)

# Lines 684-705 that need to be replaced
old_lines = [684, 706]  # 1-indexed: lines 684 to 705 inclusive

with open('apps/dashboard/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Replace lines 684-705 (0-indexed: 683-704)
new_lines = lines[:683] + [new_fallback] + lines[705:]

with open('apps/dashboard/views.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("SUCCESS: Fallback prototype replaced with HSV-based detection")

# Verify
with open('apps/dashboard/views.py', 'r', encoding='utf-8') as f:
    content = f.read()
if 'FALLBACK: Jika model gagal, pakai HSV' in content:
    print("VERIFIED: New fallback is in place")
else:
    print("ERROR: New fallback NOT found")
