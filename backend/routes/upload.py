"""
Upload & OCR route.
POST /api/v1/upload  — accepts image, returns extracted medicine names + alternatives.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from backend.database.db import get_db, SearchHistory, User
from backend.services.ocr import extract_text_from_image
from backend.services.nlp import extract_medicine_details
from backend.services.matcher import bulk_find_alternatives, MedicineMatch, AlternativeResult
from backend.routes.auth import get_current_user

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ── Pydantic response models ─────────────────────────────────────────────────

class AlternativeOut(BaseModel):
    brand_name: str
    generic_name: str
    salt_composition: str
    manufacturer: str
    brand_price: float
    generic_price: float
    jan_aushadhi_price: Optional[float]
    unit_type: str
    category: str
    strength: str
    form: str
    savings_vs_brand: float
    savings_pct: float
    source: str = "local_csv"
    source_urls: List[str] = Field(default_factory=list)
    price_available: bool = True


class MedicineMatchOut(BaseModel):
    query: str
    matched_brand: Optional[str]
    salt_composition: Optional[str]
    match_type: str
    fuzzy_score: int
    alternatives: List[AlternativeOut]
    error: Optional[str]


class OCRLineOut(BaseModel):
    text: str
    confidence: int
    bbox: Optional[List[float]] = None
    source: Optional[str] = None


class MedicineExtractionOut(BaseModel):
    name: str
    form: Optional[str] = None
    dosage: Optional[str] = None
    source_line: Optional[str] = None
    confidence: Optional[str] = None


class UploadResponse(BaseModel):
    session_id: str
    raw_text: str
    ocr_engine: str
    ocr_confidence: int
    ocr_lines: List[OCRLineOut] = Field(default_factory=list)
    ocr_processing_steps: List[str] = Field(default_factory=list)
    image_size: Optional[dict] = None
    extracted_medicines: List[str]
    extracted_medicine_details: List[MedicineExtractionOut] = Field(default_factory=list)
    results: List[MedicineMatchOut]
    total_medicines_found: int


# ── helpers ──────────────────────────────────────────────────────────────────

def _alt_to_out(a: AlternativeResult) -> AlternativeOut:
    return AlternativeOut(
        brand_name=a.brand_name,
        generic_name=a.generic_name,
        salt_composition=a.salt_composition,
        manufacturer=a.manufacturer,
        brand_price=a.brand_price,
        generic_price=a.generic_price,
        jan_aushadhi_price=a.jan_aushadhi_price,
        unit_type=a.unit_type,
        category=a.category,
        strength=a.strength,
        form=a.form,
        savings_vs_brand=a.savings_vs_brand,
        savings_pct=a.savings_pct,
        source=a.source,
        source_urls=a.source_urls,
        price_available=a.price_available,
    )


def _match_to_out(m: MedicineMatch) -> MedicineMatchOut:
    return MedicineMatchOut(
        query=m.query,
        matched_brand=m.matched_brand,
        salt_composition=m.salt_composition,
        match_type=m.match_type,
        fuzzy_score=m.fuzzy_score,
        alternatives=[_alt_to_out(a) for a in m.alternatives],
        error=m.error,
    )


# ── routes ───────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_prescription(
    file: UploadFile = File(...),
    ocr_engine: str = Form("auto"),
    db=Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Upload a prescription image (JPG / PNG / WebP / BMP).
    Returns OCR text, extracted medicine names, and cheaper alternatives.
    """
    # Validate file type
    allowed = {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"}
    ct = (file.content_type or "").lower()
    if ct not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ct}'. Upload JPG, PNG, WebP, BMP, or TIFF.",
        )

    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB).")

    # OCR
    ocr_result = await run_in_threadpool(extract_text_from_image, raw, ocr_engine)
    if ocr_result.get("error") and not ocr_result.get("text"):
        raise HTTPException(status_code=422, detail=f"OCR failed: {ocr_result['error']}")

    raw_text = ocr_result.get("text", "")

    # NLP — extract medicine names
    medicine_details = extract_medicine_details(raw_text)
    medicines_found = [m["name"] for m in medicine_details if m.get("name")]

    # Match & price
    matches = bulk_find_alternatives(medicines_found, db)

    # Save to history
    session_id = str(uuid.uuid4())
    history = SearchHistory(
        medicines_searched=", ".join(medicines_found),
        session_id=session_id,
        user_id=current_user.id if current_user else None,
    )
    db.add(history)
    db.commit()

    return UploadResponse(
        session_id=session_id,
        raw_text=raw_text,
        ocr_engine=ocr_result.get("engine_used", "none"),
        ocr_confidence=ocr_result.get("confidence", 0),
        ocr_lines=ocr_result.get("lines", []),
        ocr_processing_steps=ocr_result.get("processing_steps", []),
        image_size=ocr_result.get("image_size"),
        extracted_medicines=medicines_found,
        extracted_medicine_details=medicine_details,
        results=[_match_to_out(m) for m in matches],
        total_medicines_found=len(medicines_found),
    )


@router.post("/search-text", response_model=UploadResponse)
async def search_by_text(
    prescription_text: str = Form(...),
    db=Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Manually enter prescription text (skip OCR).
    """
    medicine_details = extract_medicine_details(prescription_text)
    medicines_found = [m["name"] for m in medicine_details if m.get("name")]
    matches = bulk_find_alternatives(medicines_found, db)

    session_id = str(uuid.uuid4())
    history = SearchHistory(
        medicines_searched=", ".join(medicines_found),
        session_id=session_id,
        user_id=current_user.id if current_user else None,
    )
    db.add(history)
    db.commit()

    return UploadResponse(
        session_id=session_id,
        raw_text=prescription_text,
        ocr_engine="manual",
        ocr_confidence=100,
        ocr_lines=[
            {"text": line, "confidence": 100, "bbox": None, "source": "manual"}
            for line in prescription_text.splitlines()
            if line.strip()
        ],
        ocr_processing_steps=["manual-text"],
        image_size=None,
        extracted_medicines=medicines_found,
        extracted_medicine_details=medicine_details,
        results=[_match_to_out(m) for m in matches],
        total_medicines_found=len(medicines_found),
    )
