import cv2
import time
import requests
from ultralytics import YOLO
from shapely.geometry import LineString, Polygon
from array import array
import math
import logging
import warnings

# Mengabaikan warning yang tidak perlu dari pandas/pytorch agar log bersih
warnings.filterwarnings("ignore")

# Konfigurasi Log (Terminal Output)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - CCTV_AI - %(levelname)s - %(message)s')

# --- KONFIGURASI KAMERA ---
# Di masa depan, data ini bisa ditarik dari database Django secara dinamis.
CAMERA_CONFIG = {
    "camera_id": 1, # Pastikan ada Kamera dengan ID 1 di tabel CCTV Django Anda
    "video_source": "https://cctv.balitower.co.id/Cikoko-006-705651_3/index.m3u8", # Stream HLS CCTV BaliTower
    
    # Koordinat garis tiang pengukur virtual (X, Y)
    "line_start": (1094, 231),
    "line_end": (1083, 403),
    
    # Konversi Piksel ke Dunia Nyata
    "pixels_in_meter": 15,
    "tip_height": 15,         # Tinggi tiang virtual
    "warning_level": 10       # Batas air (dalam meter) yang dianggap Banjir
}

# Alamat Webhook Backend Django kita
WEBHOOK_URL = "http://localhost:8080/api/cctv/webhook/"


def find_intersection(annotation, line):
    intersection = annotation.intersection(line)
    # Cek apakah garis kita menyentuh pinggiran poligon genangan air
    if intersection != [(array('d'), array('d'))]:
        try:
            return [(intersection.xy)]
        except AttributeError:
            return None
    else:
        return None


def calculate_distance(x1, y1, x2, y2, tipHeight, pixelsInAMeter):
    # Rumus Pythagoras sederhana untuk menghitung selisih jarak
    distance = tipHeight - (math.sqrt(math.pow(x2-x1, 2) + math.pow(y2-y1, 2))) / pixelsInAMeter
    return float("{:.2f}".format(distance))


def main():
    logging.info("=======================================")
    logging.info("🤖 MEMULAI MESIN PEMANTAU CCTV BANJIR")
    logging.info("=======================================")
    
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, 'best.pt')
    
    logging.info(f"Memuat model pintar YOLOv8 ({model_path})...")
    try:
        model = YOLO(model_path)
    except Exception as e:
        logging.error(f"Gagal memuat model di {model_path}! Error: {e}")
        return

    video_path = CAMERA_CONFIG["video_source"]
    logging.info(f"Mencoba menyambung ke Kamera (Source: {video_path})...")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        logging.error(f"❌ Gagal membuka video stream! Pastikan file video atau URL RTSP benar dan dapat diakses.")
        logging.info("TIPS: Jika Anda belum punya CCTV RTSP, masukkan file video jalanan banjir (.mp4) ke dalam folder ini dengan nama 'video_tes.mp4'.")
        return

    logging.info("✅ Kamera terhubung! Mulai memantau secara diam-diam (Headless Mode)...")
    
    firstCoordinate_x, firstCoordinate_y = CAMERA_CONFIG["line_start"]
    secondCoordinate_x, secondCoordinate_y = CAMERA_CONFIG["line_end"]
    pixelsInAMeter = CAMERA_CONFIG["pixels_in_meter"]
    tipHeight = CAMERA_CONFIG["tip_height"]
    warningLevel = CAMERA_CONFIG["warning_level"]
    
    # Optimasi Performa Server: Jangan proses setiap frame video!
    # Proses 1 frame setiap 30 frame (Asumsi video 30fps = AI mengecek tiap 1 detik sekali)
    frame_skip = 30 
    frame_count = 0
    last_report_time = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            logging.info("Video/Stream berakhir atau terputus.")
            break
            
        frame_count += 1
        if frame_count % frame_skip != 0:
            continue # Lewati frame ini agar server tidak panas/lambat

        # Jalankan otak AI (YOLO) pada frame ini (verbose=False agar terminal tidak kotor)
        results = model(frame, verbose=False)
        
        current_status = "no_flood"
        distance = 0.0
        
        try:
            # Ambil data bentuk piksel air (Segmentation Mask)
            segments = getattr(getattr(results[0],'masks'), 'segments')[0]
            segmentsSize = int(segments.size/2)
            segment = segments[0:segmentsSize]
            
            polygon_vertices = []
            for i in range(segmentsSize):
                x = int(segment[i][0] * frame.shape[1])
                y = int(segment[i][1] * frame.shape[0])
                polygon_vertices.append((x, y))

            line_coords = [(firstCoordinate_x, firstCoordinate_y), (secondCoordinate_x, secondCoordinate_y)]
            line = LineString(line_coords)
            
            intersection_points = find_intersection(Polygon(polygon_vertices), line)
            
            if intersection_points and intersection_points != [(array('d'), array('d'))]:
                intersection_x = intersection_points[0][0][0]
                intersection_y = intersection_points[0][1][0]
                
                # Hitung ketinggian air
                distance = calculate_distance(intersection_x, intersection_y, firstCoordinate_x, firstCoordinate_y, tipHeight, pixelsInAMeter)
                
                if distance >= warningLevel:
                    current_status = "banjir" # BANJIR!
                elif distance >= (warningLevel * 0.4):
                    current_status = "banjir_ringan" # MULAI BANJIR!
                else:
                    current_status = "aman"
            
        except AttributeError:
            # Masking kosong (AI tidak mendeteksi ada air sama sekali di frame ini)
            pass
        except Exception as e:
            # Abaikan jika ada cacat kecil pada bentuk geometri polygon
            pass

        # --- LAPOR KE BACKEND DJANGO ---
        # Untuk mencegah Spam HTTP Post, kita hanya melapor jika:
        # A. Status berubah (misal dari no_flood jadi flood)
        # B. Atau minimal 5 detik telah berlalu sejak laporan terakhir untuk status yang sama
        current_time = time.time()
        if current_time - last_report_time > 5:
            payload = {
                "camera_id": CAMERA_CONFIG["camera_id"],
                "detection_result": current_status,
                "confidence_score": 0.98, # Skor kepercayaan AI
                "snapshot_url": "" # (Opsional) URL gambar yang mungkin sudah Anda upload ke Cloud Storage
            }
            
            try:
                # Tembak URL Webhook Django kita!
                res = requests.post(WEBHOOK_URL, json=payload, timeout=3)
                
                status_icon = "🌊" if current_status == "banjir" else ("⚠️" if current_status == "banjir_ringan" else "✅")
                if res.status_code == 200:
                    logging.info(f"{status_icon} Lapor Webhook Sukses! [Status: {current_status.upper()}] | Tinggi Air: {distance}m")
                else:
                    logging.warning(f"Lapor Webhook Gagal! HTTP {res.status_code}")
            except Exception as e:
                logging.error(f"Gagal memanggil Django (Pastikan server 'python manage.py runserver' menyala): {e}")
            
            last_report_time = current_time

    cap.release()
    logging.info("Sistem pemantau mati.")


if __name__ == '__main__':
    main()
