"""
OCR service.

Uses an optional vision LLM for handwritten prescriptions, then falls back to
Tesseract and EasyOCR with multiple image preprocessing passes. The public
response includes scan details that the UI can use to explain what was read.
"""
from __future__ import annotations

import base64
import csv
import io
import logging
import os
import re
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

_easyocr_reader = None
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_MEDICINE_CSV = _PROJECT_ROOT / "data" / "medicines.csv"


def _get_easyocr():
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr  # type: ignore

            _easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        except Exception as e:
            logger.warning("EasyOCR unavailable: %s", e)
    return _easyocr_reader


def _resize_for_ocr(img: Image.Image) -> Image.Image:
    width, height = img.size
    longest = max(width, height)
    if longest >= 1800:
        return img
    scale = min(2.5, 1800 / max(1, longest))
    return img.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)


def _preprocess_variants(img: Image.Image) -> List[Tuple[str, Image.Image]]:
    """Return OCR-friendly versions ordered from conservative to aggressive."""
    base = _resize_for_ocr(img.convert("RGB"))
    gray = base.convert("L")
    enhanced = ImageEnhance.Contrast(gray).enhance(2.2)
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(2.0)
    denoised = enhanced.filter(ImageFilter.MedianFilter(size=3))

    variants = [("enhanced", denoised)]

    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        arr = np.array(denoised)
        thresh = cv2.adaptiveThreshold(
            arr,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11,
        )
        variants.append(("adaptive-threshold", Image.fromarray(thresh)))

        inverted = cv2.bitwise_not(thresh)
        variants.append(("inverted-threshold", Image.fromarray(inverted)))
    except Exception as e:
        logger.debug("OpenCV preprocessing skipped: %s", e)

    variants.append(("original", base))
    return variants


def _img_to_jpeg_bytes(image_bytes: bytes) -> tuple[bytes, str]:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=95)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return image_bytes, "image/jpeg"


def _clean_text(text: str) -> str:
    lines = []
    for line in text.replace("\r", "\n").split("\n"):
        cleaned = re.sub(r"[ \t]+", " ", line).strip()
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def _score_text(text: str, confidence: int) -> float:
    words = re.findall(r"[A-Za-z][A-Za-z0-9+-]{2,}", text)
    dosage_hits = re.findall(r"\b\d+\s*(?:mg|mcg|ml|g|iu)\b", text, flags=re.I)
    medicine_hits = _medicine_hit_count(text)
    noise_hits = len(re.findall(r"\b(?:phone|mobile|age|sex|address|clinic|doctor)\b", text, re.I))
    return len(words) * 6 + len(dosage_hits) * 16 + medicine_hits * 45 + confidence - noise_hits * 18


@lru_cache(maxsize=1)
def _medicine_keys() -> List[str]:
    names: List[str] = []
    try:
        with _MEDICINE_CSV.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                names.append(row.get("brand_name", ""))
                names.append(row.get("generic_name", ""))
    except Exception as e:
        logger.debug("Medicine scoring lexicon unavailable: %s", e)
    keys = sorted({_normalise_key(name) for name in names if len(str(name).strip()) >= 3})
    return [key for key in keys if key]


def _medicine_hit_count(text: str) -> int:
    text_key = _normalise_key(text)
    if not text_key:
        return 0
    return sum(1 for key in _medicine_keys() if len(key) >= 4 and key in text_key)


def _normalise_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def extract_text_from_image(image_bytes: bytes, engine: str = "auto") -> dict:
    """
    Extract raw text from image bytes.

    Returns keys: text, engine_used, confidence, error, lines, image_size,
    processing_steps.
    """
    result: Dict[str, Any] = {
        "text": "",
        "engine_used": "",
        "confidence": 0,
        "error": None,
        "lines": [],
        "image_size": None,
        "processing_steps": [],
    }

    try:
        img = Image.open(io.BytesIO(image_bytes))
        result["image_size"] = {"width": img.width, "height": img.height}
    except Exception as e:
        result["error"] = f"Cannot open image: {e}"
        return result

    if engine in ("auto", "gemini", "llm"):
        text, conf, lines = _try_gemini(image_bytes)
        if text.strip():
            result.update(
                text=_clean_text(text),
                engine_used="gemini-vision",
                confidence=conf,
                lines=lines,
                processing_steps=["vision-llm-transcription"],
            )
            return result
        if engine in ("gemini", "llm"):
            result["error"] = "Vision LLM could not extract text. Check GEMINI_API_KEY."
            return result

    attempts: List[Dict[str, Any]] = []
    variants = _preprocess_variants(img)

    if engine in ("auto", "tesseract"):
        for variant_name, variant_img in variants:
            for psm in (6, 11, 4):
                text, conf, lines = _try_tesseract(variant_img, psm=psm)
                attempts.append(
                    {
                        "engine": "tesseract",
                        "variant": f"{variant_name}-psm{psm}",
                        "text": text,
                        "confidence": conf,
                        "lines": lines,
                        "score": _score_text(text, conf),
                    }
                )

    if engine in ("auto", "easyocr"):
        text, conf, lines = _try_easyocr(image_bytes)
        attempts.append(
            {
                "engine": "easyocr",
                "variant": "original",
                "text": text,
                "confidence": conf,
                "lines": lines,
                "score": _score_text(text, conf),
            }
        )

    best = max(attempts, key=lambda item: item["score"], default=None)
    result["processing_steps"] = [
        f"{a['engine']}:{a['variant']}:{a['confidence']}%" for a in attempts
    ]

    if best and best["text"].strip():
        result.update(
            text=_clean_text(best["text"]),
            engine_used=f"{best['engine']}:{best['variant']}",
            confidence=int(best["confidence"]),
            lines=best["lines"],
        )
        return result

    result["error"] = _ocr_failure_message(attempts)
    return result


def _ocr_failure_message(attempts: List[Dict[str, Any]]) -> str:
    api_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
    if os.getenv("VERCEL") and not api_key:
        return (
            "No text could be extracted from the image. On Vercel, local OCR engines "
            "like Tesseract/EasyOCR are not available in this deployment. Add "
            "GEMINI_API_KEY in Vercel Environment Variables to enable cloud vision OCR, "
            "or use Search Medicine/manual text search."
        )
    if attempts and all(not a.get("text") for a in attempts):
        return (
            "No text could be extracted from the image. Try a clearer, brighter photo "
            "or enable cloud vision OCR with GEMINI_API_KEY."
        )
    return "No text could be extracted from the image."


def _try_gemini(image_bytes: bytes) -> tuple[str, int, List[dict]]:
    api_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", "")).strip().strip('"').strip("'")
    print(f"[_try_gemini] API KEY LOADED: {api_key[:6]}... (len={len(api_key)})", flush=True)
    if not api_key:
        logger.debug("GEMINI_API_KEY / GOOGLE_API_KEY not set; skipping vision LLM")
        return "", 0, []

    try:
        import requests

        jpeg_bytes, media_type = _img_to_jpeg_bytes(image_bytes)
        b64 = base64.b64encode(jpeg_bytes).decode("utf-8")
        model = os.environ.get("MEDICO_VISION_MODEL", "gemini-1.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "Transcribe this medical prescription. Preserve line breaks. "
                                "Include medicine names, strengths, forms, and instructions. "
                                "Do not add commentary or medical advice."
                            )
                        },
                        {
                            "inlineData": {
                                "mimeType": media_type,
                                "data": b64
                            }
                        }
                    ]
                }
            ]
        }

        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        if response.status_code != 200:
            logger.warning("Gemini Vision API returned status %s: %s", response.status_code, response.text)
            return "", 0, []

        resp_json = response.json()
        try:
            text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as err:
            logger.warning("Failed to parse Gemini Vision response: %s (Response: %s)", err, resp_json)
            return "", 0, []

        cleaned = _clean_text(text)
        lines = [
            {"text": line, "confidence": 95, "bbox": None, "source": "vision-llm"}
            for line in cleaned.split("\n")
            if line.strip()
        ]
        return cleaned, 95, lines
    except Exception as e:
        logger.warning("Gemini Vision API failed: %s", e)
        return "", 0, []


def _try_tesseract(img: Image.Image, psm: int = 6) -> tuple[str, int, List[dict]]:
    try:
        import pytesseract  # type: ignore
        from pytesseract import Output  # type: ignore

        data = pytesseract.image_to_data(
            img,
            config=f"--oem 3 --psm {psm}",
            output_type=Output.DICT,
        )
        grouped: Dict[Tuple[int, int, int], dict] = {}
        words: List[str] = []
        confidences: List[int] = []

        for i, raw_word in enumerate(data.get("text", [])):
            word = str(raw_word).strip()
            if not word:
                continue
            try:
                conf = int(float(data["conf"][i]))
            except Exception:
                conf = -1
            if conf < 0:
                continue

            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            item = grouped.setdefault(
                key,
                {"words": [], "conf": [], "left": [], "top": [], "right": [], "bottom": []},
            )
            item["words"].append(word)
            item["conf"].append(conf)
            item["left"].append(int(data["left"][i]))
            item["top"].append(int(data["top"][i]))
            item["right"].append(int(data["left"][i]) + int(data["width"][i]))
            item["bottom"].append(int(data["top"][i]) + int(data["height"][i]))
            words.append(word)
            confidences.append(conf)

        lines = []
        for item in grouped.values():
            text = " ".join(item["words"]).strip()
            if not text:
                continue
            avg = int(sum(item["conf"]) / max(1, len(item["conf"])))
            lines.append(
                {
                    "text": text,
                    "confidence": avg,
                    "bbox": [
                        min(item["left"]),
                        min(item["top"]),
                        max(item["right"]) - min(item["left"]),
                        max(item["bottom"]) - min(item["top"]),
                    ],
                    "source": "tesseract",
                }
            )

        text = "\n".join(line["text"] for line in lines) or " ".join(words)
        avg_conf = int(sum(confidences) / max(1, len(confidences))) if confidences else 0
        return text, avg_conf, lines
    except Exception as e:
        logger.debug("pytesseract data failed: %s", e)

    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        img.save(tmp_path)
        try:
            import subprocess

            completed = subprocess.run(
                ["tesseract", tmp_path, "stdout", "--oem", "3", "--psm", str(psm)],
                capture_output=True,
                timeout=30,
            )
            text = completed.stdout.decode("utf-8", errors="replace").strip()
            lines = [
                {"text": line, "confidence": 75, "bbox": None, "source": "tesseract"}
                for line in _clean_text(text).split("\n")
                if line.strip()
            ]
            return text, 75 if text else 0, lines
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    except Exception as e:
        logger.debug("Tesseract failed: %s", e)
        return "", 0, []


def _try_easyocr(image_bytes: bytes) -> tuple[str, int, List[dict]]:
    reader = _get_easyocr()
    if reader is None:
        return "", 0, []

    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        img_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img_cv = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        results = reader.readtext(img_cv, paragraph=False)
        if not results:
            return "", 0, []

        lines = []
        confidences = []
        for bbox, text, conf in results:
            xs = [int(point[0]) for point in bbox]
            ys = [int(point[1]) for point in bbox]
            confidence = int(float(conf) * 100)
            lines.append(
                {
                    "text": str(text).strip(),
                    "confidence": confidence,
                    "bbox": [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)],
                    "source": "easyocr",
                }
            )
            confidences.append(confidence)

        lines = _sort_ocr_lines(lines)
        combined = "\n".join(line["text"] for line in lines if line["text"])
        avg_conf = int(sum(confidences) / max(1, len(confidences)))
        return combined, avg_conf, lines
    except Exception as e:
        logger.debug("EasyOCR failed: %s", e)
        return "", 0, []


def _sort_ocr_lines(lines: List[dict]) -> List[dict]:
    def key(line: dict) -> tuple[int, int]:
        bbox = line.get("bbox") or [0, 0, 0, 0]
        try:
            top = int(bbox[1])
            left = int(bbox[0])
        except Exception:
            return (0, 0)
        # Bucket nearby baselines so words from the same row stay together.
        return (top // 12, left)

    return sorted(lines, key=key)
