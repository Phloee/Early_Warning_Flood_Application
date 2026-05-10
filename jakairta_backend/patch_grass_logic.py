"""
Patch analyze_sim: gabungkan hasil grass_submerged ke dalam logika
status_banjir, water_area_ratio, recommendation, dan response JSON.
"""

with open('apps/dashboard/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ── Replace status determination block in analyze_sim ──
old_status = (
    "        if has_water:\n"
    "            if water_area_ratio > 15:\n"
    "                status_banjir = 'BANJIR'\n"
    "                is_flood = True\n"
    "            elif water_area_ratio > 5:\n"
    "                status_banjir = 'BANJIR RINGAN'\n"
    "                is_flood = True\n"
    "            else:\n"
    "                status_banjir = 'HANYA GENANGAN'\n"
    "                is_flood = has_water and water_area_ratio > 5\n"
    "        else:\n"
    "            status_banjir = 'AMAN (TIDAK BANJIR)'\n"
    "            is_flood = False\n"
    "\n"
    "        # Import log model & simpan ke database\n"
    "        from apps.cctv.models import FloodAnalysisLog\n"
)

new_status = (
    "        # ════ GRASS REFERENCE: Override status jika rumput tenggelam ════\n"
    "        if grass_found and grass_submerged:\n"
    "            # Rumput tenggelam = BANJIR KONFIRMASI dari patokan lapangan\n"
    "            has_water = True\n"
    "            # Pastikan water_area_ratio setidaknya mencerminkan area zona rumput\n"
    "            if grass_zone:\n"
    "                grass_area_pct = (grass_zone['w'] / 100) * (grass_zone['h'] / 100) * 100\n"
    "                water_area_ratio = max(water_area_ratio, min(60.0, grass_area_pct + grass_water_pct * 0.5))\n"
    "            # Tambahkan bounding box zona rumput ke detections\n"
    "            if grass_zone:\n"
    "                detections.append({\n"
    "                    'class': 'grass_submerged',\n"
    "                    'confidence': round(grass_water_pct, 1),\n"
    "                    'box': {'x': grass_zone['x'], 'y': grass_zone['y'],\n"
    "                            'w': grass_zone['w'], 'h': grass_zone['h']},\n"
    "                    'label': f'Rumput Tenggelam ({grass_water_pct:.0f}% air)',\n"
    "                })\n"
    "            status_banjir = 'BANJIR'\n"
    "            is_flood = True\n"
    "            recommendation = 'BERBAHAYA — Rumput patokan sudah tenggelam! Segera evakuasi.'\n"
    "            risk_level = 'critical'\n"
    "            rain_intensity = 'Hujan Deras (Patokan Rumput)'\n"
    "            water_level_text = f'Rumput Tenggelam ({grass_water_pct:.0f}% air di zona patokan)'\n"
    "        elif grass_found and not grass_submerged:\n"
    "            # Rumput masih terlihat = AMAN dari sisi patokan lapangan\n"
    "            # Override hanya jika YOLO tidak mendeteksi genangan signifikan\n"
    "            if water_area_ratio < 15 and not (has_water and water_area_ratio > 10):\n"
    "                has_water = False\n"
    "                water_area_ratio = 0.0\n"
    "                status_banjir = 'AMAN (TIDAK BANJIR)'\n"
    "                is_flood = False\n"
    "                recommendation = 'AMAN — Rumput patokan masih terlihat, tidak ada banjir.'\n"
    "                risk_level = 'safe'\n"
    "                rain_intensity = 'Tidak Ada Hujan'\n"
    "                water_level_text = f'Tidak terdeteksi (Rumput: {grass_green_pct:.0f}% hijau)'\n"
    "            else:\n"
    "                # YOLO mendeteksi genangan signifikan meskipun rumput masih ada\n"
    "                if has_water:\n"
    "                    if water_area_ratio > 15:\n"
    "                        status_banjir = 'BANJIR'\n"
    "                        is_flood = True\n"
    "                    elif water_area_ratio > 5:\n"
    "                        status_banjir = 'BANJIR RINGAN'\n"
    "                        is_flood = True\n"
    "                    else:\n"
    "                        status_banjir = 'HANYA GENANGAN'\n"
    "                        is_flood = False\n"
    "                else:\n"
    "                    status_banjir = 'AMAN (TIDAK BANJIR)'\n"
    "                    is_flood = False\n"
    "        else:\n"
    "            # Tidak ada rumput di video → fallback ke logika YOLO\n"
    "            if has_water:\n"
    "                if water_area_ratio > 15:\n"
    "                    status_banjir = 'BANJIR'\n"
    "                    is_flood = True\n"
    "                elif water_area_ratio > 5:\n"
    "                    status_banjir = 'BANJIR RINGAN'\n"
    "                    is_flood = True\n"
    "                else:\n"
    "                    status_banjir = 'HANYA GENANGAN'\n"
    "                    is_flood = has_water and water_area_ratio > 5\n"
    "            else:\n"
    "                status_banjir = 'AMAN (TIDAK BANJIR)'\n"
    "                is_flood = False\n"
    "        # ═══════════════════════════════════════════════════════════\n"
    "\n"
    "        # Import log model & simpan ke database\n"
    "        from apps.cctv.models import FloodAnalysisLog\n"
)

if old_status in content:
    content = content.replace(old_status, new_status, 1)
    print("OK: status_banjir block replaced with grass-aware logic")
else:
    print("ERROR: status block not found")
    # Show what's near that area
    idx = content.find("status_banjir = 'BANJIR'\n                is_flood = True\n            elif water_area_ratio > 5:")
    print(f"Search idx: {idx}")

# ── Add grass info to JSON response ──
old_response = (
    "        return JsonResponse({\n"
    "            'success': True,\n"
    "            'camera_name': f\"Simulasi: {sim.title}\",\n"
    "            'frame_size': f'{width}x{height}',\n"
    "            'total_objects': len(detections),\n"
    "            'detections': detections,\n"
    "            'has_water': has_water,\n"
    "            'water_area_ratio': water_area_ratio,\n"
    "            'water_level_text': water_level_text,\n"
    "            'rain_intensity': rain_intensity,\n"
    "            'recommendation': recommendation,\n"
    "            'risk_level': risk_level,\n"
    "            'is_flood': is_flood,\n"
    "            'status_banjir': status_banjir,\n"
    "            'flood_probability_24h': FloodAnalysisLog.get_location_flood_probability(sim.area, hours=24),\n"
    "            'analyzed_at': timezone.now().strftime('%H:%M:%S WIB'),\n"
    "        })\n"
    "\n"
    "    except VideoSimulasi.DoesNotExist:"
)
new_response = (
    "        return JsonResponse({\n"
    "            'success': True,\n"
    "            'camera_name': f\"Simulasi: {sim.title}\",\n"
    "            'frame_size': f'{width}x{height}',\n"
    "            'total_objects': len(detections),\n"
    "            'detections': detections,\n"
    "            'has_water': has_water,\n"
    "            'water_area_ratio': water_area_ratio,\n"
    "            'water_level_text': water_level_text,\n"
    "            'rain_intensity': rain_intensity,\n"
    "            'recommendation': recommendation,\n"
    "            'risk_level': risk_level,\n"
    "            'is_flood': is_flood,\n"
    "            'status_banjir': status_banjir,\n"
    "            'flood_probability_24h': FloodAnalysisLog.get_location_flood_probability(sim.area, hours=24),\n"
    "            'analyzed_at': timezone.now().strftime('%H:%M:%S WIB'),\n"
    "            'grass_reference': {\n"
    "                'found': grass_found,\n"
    "                'submerged': grass_submerged,\n"
    "                'green_pct': grass_green_pct,\n"
    "                'water_pct': grass_water_pct,\n"
    "                'zone': grass_zone,\n"
    "                'status': 'TENGGELAM' if grass_submerged else ('AMAN' if grass_found else 'TIDAK DITEMUKAN'),\n"
    "            },\n"
    "        })\n"
    "\n"
    "    except VideoSimulasi.DoesNotExist:"
)

if old_response in content:
    content = content.replace(old_response, new_response, 1)
    print("OK: grass_reference added to JSON response")
else:
    print("WARN: response pattern not found exactly")

with open('apps/dashboard/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done.")
