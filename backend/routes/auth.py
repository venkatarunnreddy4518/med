"""
Authentication routes for lightweight accounts.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import base64
import json
import time
import os
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field, field_validator

from backend.database.db import User, SearchHistory, get_db

logger = logging.getLogger(__name__)

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "medico-ai-super-secret-key-12345")


class AuthIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        email = value.lower().strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            raise ValueError("Enter a valid email address.")
        return email


class SignupIn(AuthIn):
    name: str = Field(min_length=1, max_length=80)


class AuthOut(BaseModel):
    id: int
    name: str
    email: str
    token: str


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
        check = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
        return hmac.compare_digest(check.hex(), digest)
    except Exception:
        return False


def encode_jwt(payload: dict) -> str:
    # 1 year expiration by default for easy demo/industrial UX
    payload = dict(payload)
    if "exp" not in payload:
        payload["exp"] = int(time.time()) + 365 * 24 * 3600
        
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_jwt(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token parts count")
        header_b64, payload_b64, signature_b64 = parts
        
        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")
        
        if not hmac.compare_digest(signature_b64, expected_sig_b64):
            raise ValueError("Signature check failed")
            
        # Decode payload
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += "=" * (4 - rem)
        payload_data = base64.urlsafe_b64decode(payload_b64.encode()).decode()
        payload = json.loads(payload_data)
        
        if "exp" in payload and payload["exp"] < time.time():
            raise ValueError("Token expired")
            
        return payload
    except Exception as e:
        logger.warning(f"JWT decode failed: {e}")
        return {}


def get_current_user(authorization: Optional[str] = Header(None), db=Depends(get_db)) -> Optional[User]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    payload = decode_jwt(token)
    if not payload or "user_id" not in payload:
        return None
    return db.query(User).filter(User.id == payload["user_id"]).first()


def require_current_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required or token expired.")
    return current_user


def _auth_out(user: User) -> AuthOut:
    token = encode_jwt({"user_id": user.id, "name": user.name, "email": user.email})
    return AuthOut(
        id=user.id,
        name=user.name,
        email=user.email,
        token=token,
    )


@router.post("/auth/signup", response_model=AuthOut)
def signup(payload: SignupIn, db=Depends(get_db)):
    email = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account already exists for this email.")

    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=_hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _auth_out(user)


@router.post("/auth/login", response_model=AuthOut)
def login(payload: AuthIn, db=Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return _auth_out(user)


@router.get("/auth/history")
def get_user_history(
    current_user: User = Depends(require_current_user),
    db=Depends(get_db)
):
    history = db.query(SearchHistory).filter(SearchHistory.user_id == current_user.id).order_by(SearchHistory.timestamp.desc()).all()
    return [
        {
            "id": h.id,
            "medicines_searched": h.medicines_searched,
            "timestamp": h.timestamp.isoformat() + "Z",
            "session_id": h.session_id,
        }
        for h in history
    ]
