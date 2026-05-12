"""Flood-analysis helpers for CCTV and simulation videos.
Uses GPT-4o Vision as primary analyzer + YOLO as fallback.
"""

from __future__ import annotations

import base64
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import cv2
import numpy as np

FLOOD_KEYWORDS = ("banjir", "flood", "water", "genangan", "siaga")
WARNING_KEYWORDS = ("siaga", "warning", "waspada", "mulai")
SAFE_KEYWORDS = ("aman", "safe", "dry", "normal")

VISION_FLOOD_PROMPT = """You are a water detection system for Jakarta flood monitoring CCTV cameras. Your ONLY job is to detect if there is ANY water visible on the ground surface in this image.

STEP 1 - SCAN THE GROUND:
Ignore all people, vehicles, buildings, and objects. Look ONLY at the ground/road/floor surface visible in this image.

STEP 2 - IDENTIFY WATER SIGNS ON GROUND:
Water on ground in CCTV footage appears as:
- Flat, smooth, reflective surface (like a mirror or wet tile)
- Grayish, brownish, or dark wet patches covering the road
- Shimmering or glossy texture on pavement/asphalt
- People's feet or vehicle wheels partially submerged
- Ripples or distortion on ground surface
- Puddles of any size visible on road or sidewalk
- Ground that looks flooded even partially

STEP 3 - MAKE YOUR DECISION:
If you see ANY of the above on ANY part of the ground = flood_detected: true
Only return flood_detected: false if the ground is clearly 100% dry everywhere.

STEP 4 - ESTIMATE COVERAGE:
water_ratio = fraction of visible ground area with water (0.0 to 1.0)
Small puddles=0.1, quarter=0.25, half=0.5, most=0.75, all=1.0

STEP 5 - SET STATUS:
- water_ratio >= 0.1 AND flood_detected true = status: banjir, confidence: high
- water_ratio >= 0.05 AND flood_detected true = status: banjir, confidence: medium
- flood_detected true but tiny water = status: siaga, confidence: low
- flood_detected false = status: aman

RETURN ONLY THIS JSON, NO OTHER TEXT:
{"flood_detected": true or false, "confidence": "high" or "medium" or "low", "water_ratio": 0.0, "status": "banjir" or "siaga" or "aman", "evidence": "describe exactly what you see on the ground surface"}"""


def normalize_stream_url(url: str) -> str:
    if not url:
        return url
    if "balitower.co.id" in url and "embed.html" in url:
        return url.replace("embed.html", "index.m3u8")
    return url


def get_flood_model_path(settings: Any) -> str:
    base_dir = Path(settings.BASE_DIR)
    candidates = [
        os.environ.get("FLOOD_MODEL_PATH"),
        base_dir / "models" / "flood" / "best.pt",
        base_dir / "best.pt",
        base_dir / ".." / "yolov8_flood_vision" / "best.pt",
        base_dir / ".." / "banjir (1)" / "banjir" / "best.pt",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser().resolve()
        if path.exists():
            return str(path)
    checked = ", ".join(str(Path(c).expanduser()) for c in candidates if c)
    raise FileNotFoundError(f"Model banjir best.pt tidak ditemukan. Dicek: {checked}")


@lru_cache(maxsize=2)
def load_flood_model(model_path: str):
    from ultralytics import YOLO
    return YOLO(model_path)


def capture_frame(source: str, *, retries: int = 45):
    source = normalize_stream_url(source)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        cap.release()
        return None, source, "Stream/video tidak bisa dibuka."
    frame = None
    for _ in range(max(1, retries)):
        ok, candidate = cap.read()
        if ok and candidate is not None and candidate.size > 0:
            frame = candidate
            break
    cap.release()
    if frame is None:
        return None, source, "Gagal mengambil frame dari stream/video."
    return frame, source, None


def _frame_to_base64(frame) -> str:
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buffer).decode("utf-8")


def analyze_frame_with_gpt4vision(frame, *, openai_api_key: str) -> dict[str, Any]:
    """Send frame to GPT-4o Vision and get flood analysis."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)
        b64 = _frame_to_base64(frame)
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_FLOOD_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}},
                    ],
                }
            ],
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if any
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        flood_detected = bool(result.get("flood_detected", False))
        confidence = result.get("confidence", "low")
        water_ratio = float(result.get("water_ratio", 0.0))
        status = result.get("status", "aman")
        evidence = result.get("evidence", "")

        # Force consistency
        if flood_detected and status == "aman":
            status = "siaga"
        # Product rule after visual QA: small puddles/genangan are SIAGA, not BANJIR.
        # BANJIR requires broad visible ground coverage, not just reflective tiles/patches.
        if flood_detected:
            if water_ratio >= 0.35:
                status = "banjir"
                confidence = "high"
            else:
                status = "siaga"
                confidence = "medium" if water_ratio >= 0.05 else "low"

        is_flood = flood_detected
        return {
            "model_used": "gpt-4o-vision",
            "has_water": flood_detected,
            "flood_detected": is_flood,
            "is_flood": is_flood,
            "confidence": confidence,
            "confidence_score": 90.0 if confidence == "high" else (70.0 if confidence == "medium" else 50.0),
            "water_ratio": round(water_ratio, 3),
            "water_area_ratio": round(water_ratio * 100, 1),
            "status_banjir": status,
            "camera_status": "flood" if status == "banjir" else ("mulai_banjir" if status == "siaga" else "no_flood"),
            "risk_level": "critical" if status == "banjir" else ("warning" if status == "siaga" else "safe"),
            "evidence": evidence,
            "detections": [],
            "total_objects_detected": 0,
            "water_level_text": "Tinggi (Parah)" if status == "banjir" else ("Genangan Ringan" if status == "siaga" else "Aman"),
            "recommendation": "EVAKUASI SEGERA! Kondisi Parah." if status == "banjir" else ("Pantau kondisi, ada potensi genangan." if status == "siaga" else "Kondisi aman, tetap monitoring."),
        }
    except Exception as e:
        return {"error": str(e), "flood_detected": False, "status_banjir": "aman", "has_water": False, "is_flood": False}


def _box_to_percent(box, width: int, height: int) -> dict[str, float]:
    x1, y1, x2, y2 = box.xyxy[0].tolist()
    return {
        "x": round(x1 / width * 100, 1),
        "y": round(y1 / height * 100, 1),
        "w": round((x2 - x1) / width * 100, 1),
        "h": round((y2 - y1) / height * 100, 1),
    }


def detect_ground_water_heuristic(frame) -> dict[str, Any]:
    """Sensitive fallback for reflective/muddy water on the visible ground surface."""
    # Disabled by default: this was too aggressive on bright concrete/tiles and
    # caused dry road/empty sidewalk frames to become false BANJIR.
    if os.environ.get("ENABLE_GROUND_WATER_HEURISTIC") != "1":
        return {
            "flood_detected": False,
            "water_ratio": 0.0,
            "confidence": "low",
            "evidence": "Ground-water heuristic disabled; avoiding reflective floor/road false positives.",
        }

    height, width = frame.shape[:2]
    y0 = int(height * 0.15)
    roi = frame[y0:height, :]
    if roi.size == 0:
        return {
            "flood_detected": False,
            "water_ratio": 0.0,
            "confidence": "low",
            "evidence": "No visible ground region available for heuristic scan.",
        }

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    clear_water = (s < 70) & (v > 135)
    muddy_water = (h >= 5) & (h <= 35) & (s >= 18) & (v >= 45) & (v <= 210)
    green = (h >= 35) & (h <= 90) & (s >= 40) & (v >= 40)

    mask = ((clear_water | muddy_water) & (~green)).astype("uint8") * 255
    kernel = np.ones((7, 7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    ratio = float(cv2.countNonZero(mask)) / max(mask.shape[0] * mask.shape[1], 1)
    ratio = round(min(max(ratio, 0.0), 1.0), 3)
    flood_detected = ratio >= 0.02
    confidence = "high" if ratio >= 0.10 else ("medium" if ratio >= 0.05 else ("low" if flood_detected else "low"))
    evidence = (
        f"Ground surface scan found water-like reflective/muddy texture covering about {ratio:.2f} of visible ground."
        if flood_detected else
        "Ground surface scan did not find enough reflective/muddy water-like texture."
    )
    return {
        "flood_detected": flood_detected,
        "water_ratio": ratio,
        "confidence": confidence,
        "evidence": evidence,
    }


def analyze_frame(frame, settings: Any, *, conf: float = 0.25, area=None) -> dict[str, Any]:
    """Analyze frame: try GPT-4o Vision first, fallback to YOLO."""
    height, width = frame.shape[:2]

    # GPT vision is optional only. For this dashboard demo, the trained YOLO
    # model is the stable source of truth; GPT was too sensitive on dry but
    # reflective concrete/tiles and caused false BANJIR.
    openai_key = os.environ.get("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
    if os.environ.get("ENABLE_GPT_VISION_FLOOD") == "1" and openai_key:
        result = analyze_frame_with_gpt4vision(frame, openai_api_key=openai_key)
        if "error" not in result:
            result["frame_size"] = f"{width}x{height}"
            return result
        print(f"[vision] GPT-4o error: {result.get('error')} — falling back to YOLO")

    # Fallback: YOLO
    try:
        model_path = get_flood_model_path(settings)
    except FileNotFoundError:
        return {
            "model_used": "none",
            "has_water": False,
            "flood_detected": False,
            "is_flood": False,
            "confidence": "low",
            "confidence_score": 0.0,
            "water_ratio": 0.0,
            "water_area_ratio": 0.0,
            "status_banjir": "aman",
            "camera_status": "no_flood",
            "risk_level": "safe",
            "evidence": "No model available.",
            "detections": [],
            "total_objects_detected": 0,
            "water_level_text": "Aman",
            "recommendation": "Kondisi aman, tetap monitoring.",
            "frame_size": f"{width}x{height}",
        }

    model = load_flood_model(model_path)
    results = model(frame, conf=conf, verbose=False)

    detections = []
    banjir_area_ratio = 0.0
    warning_area_ratio = 0.0
    banjir_confidences = []
    warning_confidences = []
    safe_confidences = []

    for result in results:
        boxes = result.boxes or []
        masks = getattr(result, "masks", None)
        for idx, box in enumerate(boxes):
            confidence = float(box.conf[0])
            conf_pct = confidence * 100
            cls_name = model.names[int(box.cls[0])]
            cls_l = str(cls_name).lower()
            box_pct = _box_to_percent(box, width, height)
            is_warning = any(key in cls_l for key in WARNING_KEYWORDS)
            is_safe = any(key in cls_l for key in SAFE_KEYWORDS)
            is_banjir = any(key in cls_l for key in ("banjir", "flood", "water", "genangan")) and not is_warning and not is_safe
            is_water = (is_banjir or is_warning) and not is_safe
            area_pct = box_pct["w"] * box_pct["h"] / 100.0
            if is_water and masks is not None and getattr(masks, "data", None) is not None and idx < len(masks.data):
                mask = masks.data[idx]
                area_pct = float((mask > 0.5).sum().item()) / max(mask.numel(), 1) * 100.0
            detections.append({
                "class": cls_name,
                "confidence": round(conf_pct, 1),
                "box": box_pct,
                "area_ratio": round(area_pct, 2),
                "is_water": is_water,
                "is_warning": is_warning,
            })
            if is_safe:
                safe_confidences.append(conf_pct)
            elif is_banjir:
                banjir_area_ratio += area_pct
                banjir_confidences.append(conf_pct)
            elif is_warning:
                # `siaga` is an early-warning class. It should never escalate to
                # critical BANJIR by area alone; it only raises the frame to SIAGA.
                warning_area_ratio += area_pct
                warning_confidences.append(conf_pct)

    banjir_area_ratio = round(min(banjir_area_ratio, 100.0), 1)
    warning_area_ratio = round(min(warning_area_ratio, 100.0), 1)
    flood_area_ratio = round(min(banjir_area_ratio + warning_area_ratio, 100.0), 1)
    water_confidences = banjir_confidences + warning_confidences
    has_water = bool(water_confidences)
    avg_conf = round(sum(water_confidences) / max(len(water_confidences), 1), 1) if has_water else 0.0
    normalized_water_ratio = round(flood_area_ratio / 100.0, 3)
    max_safe_conf = max(safe_confidences, default=0.0)
    max_banjir_conf = max(banjir_confidences, default=0.0)
    max_warning_conf = max(warning_confidences, default=0.0)

    # Small dataset protection: when the model strongly sees AMAN and only weakly
    # hallucinates water/siaga, prefer AMAN to avoid false critical alerts.
    safe_dominant = max_safe_conf >= 65 and max_banjir_conf < 50 and max_warning_conf < 60

    if safe_dominant:
        status_banjir, camera_status, is_flood, risk_level, confidence_level = "aman", "no_flood", False, "safe", "medium"
        normalized_water_ratio = 0.0
        flood_area_ratio = 0.0
    elif banjir_area_ratio >= 35 and max_banjir_conf >= 60:
        status_banjir, camera_status, is_flood, risk_level, confidence_level = "banjir", "flood", True, "critical", "high"
    elif has_water and max(water_confidences, default=0) >= 45:
        status_banjir, camera_status, is_flood, risk_level, confidence_level = "siaga", "mulai_banjir", True, "warning", "medium"
    else:
        status_banjir, camera_status, is_flood, risk_level, confidence_level = "aman", "no_flood", False, "safe", "low"

    return {
        "model_used": Path(model_path).name,
        "frame_size": f"{width}x{height}",
        "detections": detections,
        "has_water": is_flood,
        "flood_detected": is_flood,
        "confidence": confidence_level,
        "is_flood": is_flood,
        "status_banjir": status_banjir,
        "camera_status": camera_status,
        "water_area_ratio": flood_area_ratio,
        "water_ratio": normalized_water_ratio,
        "risk_level": risk_level,
        "confidence_score": avg_conf,
        "evidence": (
            f"YOLO detected water covering {normalized_water_ratio:.2f} of frame."
            if is_flood else
            (f"Tiny/noisy water-like detection ({normalized_water_ratio:.2f}) ignored as below genangan threshold." if has_water else "No water detected by YOLO.")
        ),
        "total_objects_detected": len(detections),
        "water_level_text": "Tinggi" if status_banjir == "banjir" else ("Genangan Ringan" if status_banjir == "siaga" else "Aman"),
        "recommendation": "Segera evakuasi dan pantau jalur aman." if status_banjir == "banjir" else ("Pantau kondisi, ada potensi genangan." if status_banjir == "siaga" else "Kondisi aman, tetap monitoring."),
    }


def aggregate_frame_results(frame_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Finalize status after all sampled frames are analyzed."""
    valid = [r for r in frame_results if r]
    flood_frames = [r for r in valid if r.get("flood_detected") is True]
    banjir_frames = [r for r in flood_frames if str(r.get("status_banjir") or "").lower() == "banjir"]
    flood_ratio = len(flood_frames) / len(valid) if valid else 0

    best_confidence = "high" if any(r.get("confidence") == "high" for r in flood_frames) else \
        "medium" if any(r.get("confidence") == "medium" for r in flood_frames) else "low"
    max_water_ratio = max((float(r.get("water_ratio") or 0) for r in valid), default=0)
    max_banjir_ratio = max((float(r.get("water_ratio") or 0) for r in banjir_frames), default=0)
    max_banjir_conf = max((float(r.get("confidence_score") or 0) for r in banjir_frames), default=0)
    best = max(valid, key=lambda r: (float(r.get("water_ratio") or 0), float(r.get("confidence_score") or 0)), default={})

    # Final decision after all frames:
    # - BANJIR only if at least one frame is confidently classified banjir.
    # - Broad low-confidence water-like boxes remain SIAGA, not critical.
    # - Dry all frames => AMAN.
    if banjir_frames and max_banjir_ratio >= 0.35 and max_banjir_conf >= 60:
        final_status = "banjir"
    elif flood_frames:
        final_status = "siaga"
    else:
        final_status = "aman"

    if final_status == "siaga" and best_confidence == "high":
        best_confidence = "medium"
    is_flood = final_status in ("banjir", "siaga")
    if not is_flood:
        max_water_ratio = 0.0
    water_area_ratio = round(max_water_ratio * 100, 1)
    risk_level = "critical" if final_status == "banjir" else ("warning" if final_status == "siaga" else "safe")
    evidence = " | ".join(f"{r.get('frame_position', 'frame')}: {r.get('evidence', '')}" for r in valid)

    return {
        **best,
        "frame_results": valid,
        "flood_frames": len(flood_frames),
        "total_frames_sampled": len(valid),
        "flood_ratio": round(flood_ratio, 2),
        "flood_detected": is_flood,
        "is_flood": is_flood,
        "has_water": is_flood,
        "status_banjir": final_status,
        "camera_status": "flood" if final_status == "banjir" else ("mulai_banjir" if final_status == "siaga" else "no_flood"),
        "confidence": best_confidence,
        "water_ratio": round(max_water_ratio, 3),
        "water_area_ratio": water_area_ratio,
        "risk_level": risk_level,
        "evidence": evidence,
        "water_level_text": "Tinggi (Parah)" if final_status == "banjir" else ("Rendah" if final_status == "siaga" else "Aman"),
        "recommendation": "EVAKUASI SEGERA! Kondisi Parah." if final_status == "banjir" else ("Pantau kondisi, ada potensi genangan." if final_status == "siaga" else "Kondisi aman, tetap monitoring."),
        "total_objects_detected": sum(int(r.get("total_objects_detected") or 0) for r in valid),
        "confidence_score": max((float(r.get("confidence_score") or 0) for r in valid), default=0),
    }


def analyze_video_source(source: str, settings: Any, *, area=None, conf: float = 0.25, frame_positions=(0.10, 0.25, 0.50, 0.75, 0.90)):
    """Analyze 5 sampled frames from a video/stream, return one final aggregate result."""
    source = normalize_stream_url(source)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        cap.release()
        raise RuntimeError("Stream/video tidak bisa dibuka. Cek URL CCTV atau file video.")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    frame_results: list[dict[str, Any]] = []

    if total_frames > 0:
        targets = [(f"{int(p * 100)}%", max(0, min(total_frames - 1, int(total_frames * p)))) for p in frame_positions]
        for label, target in targets:
            cap.set(cv2.CAP_PROP_POS_FRAMES, target)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            result = analyze_frame(frame, settings, conf=conf, area=area)
            result["frame_position"] = label
            result["frame_number"] = target
            frame_results.append(result)
    else:
        targets = [5, 25, 50, 75, 90]
        target_idx = 0
        for i in range(1, 120):
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            if i >= targets[target_idx]:
                result = analyze_frame(frame, settings, conf=conf, area=area)
                result["frame_position"] = f"stream-{target_idx + 1}"
                result["frame_number"] = i
                frame_results.append(result)
                target_idx += 1
                if target_idx >= len(targets):
                    break

    cap.release()
    if not frame_results:
        raise RuntimeError("Gagal membaca frame video/stream.")

    aggregate = aggregate_frame_results(frame_results)
    aggregate["source_url"] = source
    aggregate["total_frames"] = total_frames
    return aggregate
