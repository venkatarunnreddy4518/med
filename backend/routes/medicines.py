"""
Medicines route — search, browse, single-medicine lookup.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from backend.database.db import get_db, Medicine, SearchHistory, User
from backend.services.matcher import find_alternatives, AlternativeResult
from backend.routes.auth import get_current_user

router = APIRouter()


class MedicineOut(BaseModel):
    id: int
    brand_name: str
    generic_name: str
    salt_composition: str
    manufacturer: str
    brand_price_per_unit: float
    generic_price_per_unit: float
    jan_aushadhi_price: Optional[float]
    unit_type: str
    category: str
    strength: str
    form: str


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


class SingleSearchResponse(BaseModel):
    query: str
    matched_brand: Optional[str]
    salt_composition: Optional[str]
    match_type: str
    fuzzy_score: int
    alternatives: List[AlternativeOut]
    error: Optional[str]


@router.get("/medicines", response_model=List[MedicineOut])
def list_medicines(
    q: Optional[str] = Query(None, description="Filter by brand/generic name"),
    category: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db=Depends(get_db),
):
    """List / search medicines in the database."""
    query = db.query(Medicine)
    if q:
        query = query.filter(
            (Medicine.brand_name.ilike(f"%{q}%")) |
            (Medicine.generic_name.ilike(f"%{q}%")) |
            (Medicine.salt_composition.ilike(f"%{q}%"))
        )
    if category:
        query = query.filter(Medicine.category.ilike(f"%{category}%"))
    total = query.count()
    medicines = query.offset(skip).limit(limit).all()
    return [
        MedicineOut(
            id=m.id,
            brand_name=m.brand_name,
            generic_name=m.generic_name,
            salt_composition=m.salt_composition,
            manufacturer=m.manufacturer,
            brand_price_per_unit=m.brand_price_per_unit,
            generic_price_per_unit=m.generic_price_per_unit,
            jan_aushadhi_price=m.jan_aushadhi_price,
            unit_type=m.unit_type,
            category=m.category,
            strength=m.strength,
            form=m.form,
        )
        for m in medicines
    ]


@router.get("/medicines/search", response_model=SingleSearchResponse)
def search_medicine(
    name: str = Query(..., description="Brand or generic medicine name"),
    db=Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Single medicine fuzzy search — returns cheapest alternatives.
    """
    match = find_alternatives(name, db)
    
    # Log search in history if authenticated
    if current_user:
        import uuid
        history = SearchHistory(
            medicines_searched=name,
            session_id=str(uuid.uuid4()),
            user_id=current_user.id,
        )
        db.add(history)
        db.commit()

    alts = [
        AlternativeOut(
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
        for a in match.alternatives
    ]
    return SingleSearchResponse(
        query=match.query,
        matched_brand=match.matched_brand,
        salt_composition=match.salt_composition,
        match_type=match.match_type,
        fuzzy_score=match.fuzzy_score,
        alternatives=alts,
        error=match.error,
    )


@router.get("/categories")
def list_categories(db=Depends(get_db)):
    """All distinct medicine categories."""
    rows = db.query(Medicine.category).distinct().all()
    return sorted(set(r[0] for r in rows if r[0]))
