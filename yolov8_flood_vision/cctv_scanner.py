import logging
import os
import time
import warnings
from pathlib import Path

import cv2
import requests
from ultralytics import YOLO

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - CCTV_AI - %(levelname)s - %(message)s')

CAMERA_CONFIG = {
    "camera_id": 1,
    "video_source": "https://cctv.balitower.co.id/Cikoko-006-705651_3/index.m3u8",
}

# Backend sekarang dijalankan via instruksi kolaborasi di port 8000.
WEBHOOK_URL = os.environ.get("CCTV_WEBHOOK_URL", "http://127.0.0.1:8000/api/cctv/webhook/")
FLOOD_KEYWORDS = ("banjir", "flood", "water", "genangan")


def resolve_model_path() -> str:
    here = Path(__file__).resolve().parent
    candidates = [
        os.environ.get("FLOOD_MODEL_PATH"),
        here / ".." / "jakairta_backend" / "models" / "flood" / "best.pt",
        here / "best.pt",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser().resolve()
        if path.exists():
            return str(path)
    raise FileNotFoundError("best.pt tidak ditemukan. Simpan model di jakairta_backend/models/flood/best.pt atau yolov8_flood_vision/best.pt")


def classify_frame(model, frame):
    results = model(frame, conf=0.25, verbose=False)
    h, w = frame.shape[:2]
    water_ratio = 0.0
    confidences = []

    for result in results:
        for box in (result.boxes or []):
            cls_name = model.names[int(box.cls[0])]
            if not any(k in str(cls_name).lower() for k in FLOOD_KEYWORDS):
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            water_ratio += max(0, (x2 - x1) * (y2 - y1)) / max(w * h, 1) * 100
            confidences.append(float(box.conf[0]) * 100)

    water_ratio = min(water_ratio, 100.0)
    confidence = sum(confidences) / max(len(confidences), 1) if confidences else 0.0

    if water_ratio >= 15 or (confidence >= 80 and water_ratio >= 5):
        return "flood", water_ratio, confidence
    if water_ratio >= 3:
        return "mulai_banjir", water_ratio, confidence
    return "no_flood", water_ratio, confidence


def main():
    logging.info("🤖 Memulai CCTV flood scanner")
    model_path = resolve_model_path()
    logging.info(f"Memuat model: {model_path}")
    model = YOLO(model_path)

    cap = cv2.VideoCapture(CAMERA_CONFIG["video_source"])
    if not cap.isOpened():
        logging.error("Gagal membuka CCTV stream/video.")
        return

    frame_skip = 30
    frame_count = 0
    last_report_time = 0

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok or frame is None:
            logging.warning("Stream terputus/berakhir.")
            break

        frame_count += 1
        if frame_count % frame_skip != 0:
            continue

        detection_result, water_ratio, confidence = classify_frame(model, frame)
        now = time.time()
        if now - last_report_time < 5:
            continue

        payload = {
            "camera_id": CAMERA_CONFIG["camera_id"],
            "detection_result": detection_result,
            "confidence_score": round(confidence / 100, 4),
            "water_area_ratio": round(water_ratio, 1),
            "snapshot_url": "",
        }
        try:
            res = requests.post(WEBHOOK_URL, json=payload, timeout=5)
            icon = "🌊" if detection_result == "flood" else ("⚠️" if detection_result == "mulai_banjir" else "✅")
            logging.info(f"{icon} Webhook {res.status_code}: {detection_result} | area={water_ratio:.1f}% | conf={confidence:.1f}%")
        except Exception as exc:
            logging.error(f"Gagal memanggil backend Django: {exc}")
        last_report_time = now

    cap.release()
    logging.info("Scanner berhenti.")


if __name__ == '__main__':
    main()
