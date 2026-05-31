"""
NLP service for prescription text.

The rule-based extractor is fast and offline. If MEDICO_USE_LLM_NLP=true and
GEMINI_API_KEY or GOOGLE_API_KEY is available, a text LLM can clean up ambiguous OCR output.
"""
from __future__ import annotations

import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from backend.services.web_medicine import lookup_web_medicine

logger = logging.getLogger(__name__)

_BEFORE_KW = re.compile(
    r"\b(?:tab(?:let)?s?|cap(?:sule)?s?|syp|syr(?:up)?|inj(?:ection)?|"
    r"susp(?:ension)?|sol(?:ution)?|oint(?:ment)?|drop(?:s)?|cream|gel|spray|"
    r"lotion|respules?|neb(?:ulizer)?|powder|rx|r/|medicine|drug)\b"
    r"\s*[:.-]?\s*",
    re.IGNORECASE,
)

_FORM_PATTERN = re.compile(
    r"\b(tab(?:let)?s?|cap(?:sule)?s?|syp|syr(?:up)?|inj(?:ection)?|"
    r"susp(?:ension)?|sol(?:ution)?|oint(?:ment)?|drop(?:s)?|cream|gel|spray|"
    r"lotion|respules?|neb(?:ulizer)?|powder)\b",
    re.IGNORECASE,
)
_DOSAGE_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|ml|mL|g|iu|IU|units?|%)"
    r"(?:\s*/\s*\d+(?:\.\d+)?\s*(?:mg|mcg|ml|mL|g|iu|IU|units?))?\b",
    re.I,
)
_FREQUENCY_PATTERN = re.compile(
    r"\b(?:od|bd|tds|qid|sos|hs|ac|pc|prn|stat|once|twice|thrice|daily|weekly|"
    r"morning|afternoon|evening|night|bedtime|before|after|meals?|food|days?|"
    r"x\s*\d+|for\s+\d+)\b",
    re.IGNORECASE,
)
_SKIP_LINE_PATTERN = re.compile(
    r"\b(?:date|age|a/?g/e|sex|gender|name|address|phone|mobile|mob|tel|contact|"
    r"dr\.?|doctor|hospital|clinic|patient|diagnosis|weight|height|bp|blood|"
    r"pressure|signature|follow|review|page|reg(?:istration)?|uhid|invoice|bill)\b",
    re.IGNORECASE,
)
_BAD_TOKEN_PATTERN = re.compile(
    r"^(?:rx|tab|tablet|cap|capsule|syp|syrup|inj|injection|take|after|before|"
    r"daily|night|morning|days|food|dose|no|nil|signature|phone|mobile|age|ahge|"
    r"name|patient|doctor|clinic|hospital|male|female|years?|yrs?|month|months?|"
    r"susp|suspension|solution|drops?|cream|gel|spray|lotion|powder)$",
    re.IGNORECASE,
)
_MEDICINE_CANDIDATE = re.compile(r"^[A-Za-z][A-Za-z0-9+-]{2,34}$")
_PHRASE_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9+-]{1,34}")
_PHONE_PATTERN = re.compile(r"(?:\+?\d[\s-]?){8,}")
_HAS_MEDICINE_CONTEXT = re.compile(
    rf"(?:{_FORM_PATTERN.pattern}|\b\d+(?:\.\d+)?\s*(?:mg|mcg|ml|g|iu|units?|%)\b)",
    re.IGNORECASE,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_MEDICINE_CSV = _PROJECT_ROOT / "data" / "medicines.csv"


def extract_medicine_details(text: str) -> List[Dict[str, Optional[str]]]:
    if not text or not text.strip():
        return []

    rule_details = _rule_extract_details(text)
    llm_details = _llm_extract_details(text) if _should_use_llm() else []
    return _merge_details(rule_details, llm_details)


def extract_medicines(text: str) -> List[str]:
    return [item["name"] for item in extract_medicine_details(text) if item.get("name")]


def _rule_extract_details(text: str) -> List[Dict[str, Optional[str]]]:
    details: List[Dict[str, Optional[str]]] = []
    for raw_line in text.replace("\r", "\n").split("\n"):
        line = re.sub(r"\s+", " ", raw_line).strip()
        if _should_skip_line(line):
            continue

        form = _extract_form(line)
        line_dosage = _extract_dosage(line)
        has_context = bool(_HAS_MEDICINE_CONTEXT.search(line))
        details.extend(_known_medicines_from_line(line, form, line_dosage))

        if not has_context:
            continue

        phrase_detail = _fallback_medicine_from_line(line, form, line_dosage)
        if phrase_detail:
            details.append(phrase_detail)

        working = _BEFORE_KW.sub(" ", line)
        working = _DOSAGE_PATTERN.sub(" ", working)
        working = _FREQUENCY_PATTERN.sub(" ", working)
        working = re.sub(r"\b\d+\b", " ", working)

        tokens = [re.sub(r"[^A-Za-z0-9+-]", "", tok) for tok in working.split()]
        for token in tokens:
            if not _is_candidate(token):
                continue
            corrected = _correct_to_known_medicine(token, require_strong=False)
            if not corrected:
                continue
            name, score = corrected
            details.append(
                {
                    "name": name,
                    "form": form,
                    "dosage": _nearest_dosage(line, token) or line_dosage,
                    "source_line": line,
                    "confidence": "db-exact" if score == 100 else f"db-fuzzy-{score}",
                }
            )

    return _dedupe_details(details)


def _should_use_llm() -> bool:
    enabled = os.environ.get("MEDICO_USE_LLM_NLP", "").strip().lower()
    api_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", "")).strip().strip('"').strip("'")
    return enabled in {"1", "true", "yes", "on"} and bool(api_key)


def _llm_extract_details(text: str) -> List[Dict[str, Optional[str]]]:
    api_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", "")).strip().strip('"').strip("'")
    if not api_key:
        return []
    try:
        import requests

        model = os.environ.get("MEDICO_TEXT_MODEL", "gemini-1.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        prompt = (
            "Extract only medicine entries from this OCR prescription text. "
            "Return strict JSON only: "
            "[{\"name\":\"brand or generic\",\"form\":\"tablet/capsule/etc or null\","
            "\"dosage\":\"strength or null\",\"source_line\":\"line from OCR\"}]. "
            "Ignore doctor names, diagnosis, dates, and instructions.\n\n"
            f"{text[:5000]}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        if response.status_code != 200:
            logger.warning("Gemini NLP API returned status %s: %s", response.status_code, response.text)
            return []

        resp_json = response.json()
        try:
            content = resp_json["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            content = "[]"

        payload_data = json.loads(_json_slice(content))
        if not isinstance(payload_data, list):
            return []

        details: List[Dict[str, Optional[str]]] = []
        for item in payload_data:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not _is_candidate(name.replace(" ", "")):
                continue
            details.append(
                {
                    "name": _normalise(name),
                    "form": _blank_to_none(item.get("form")),
                    "dosage": _blank_to_none(item.get("dosage")),
                    "source_line": _blank_to_none(item.get("source_line")),
                    "confidence": "llm",
                }
            )
        return _dedupe_details(details)
    except Exception as e:
        logger.warning("Gemini LLM medicine extraction failed: %s", e)
        return []


def _merge_details(
    rule_details: List[Dict[str, Optional[str]]],
    llm_details: List[Dict[str, Optional[str]]],
) -> List[Dict[str, Optional[str]]]:
    merged = list(rule_details)
    existing = {str(item.get("name", "")).lower() for item in merged}
    for item in llm_details:
        key = str(item.get("name", "")).lower()
        if key and key not in existing:
            merged.append(item)
            existing.add(key)
    return _dedupe_details(merged)


def _should_skip_line(line: str) -> bool:
    if not line or len(line) < 3:
        return True
    lower = line.lower()
    if _SKIP_LINE_PATTERN.search(line):
        return True
    if _PHONE_PATTERN.search(line) and not _DOSAGE_PATTERN.search(line):
        return True
    if re.search(r"\b(?:age|ahge|yrs?|years?)\b", lower):
        return True
    return False


@lru_cache(maxsize=1)
def _medicine_lexicon() -> List[str]:
    names: List[str] = []
    try:
        import pandas as pd  # type: ignore

        df = pd.read_csv(_MEDICINE_CSV)
        for column in ("brand_name", "generic_name"):
            if column not in df.columns:
                continue
            names.extend(str(value).strip() for value in df[column].dropna().tolist())
    except Exception as e:
        logger.warning("Medicine lexicon unavailable: %s", e)

    seen: set[str] = set()
    unique: List[str] = []
    for name in names:
        if len(name) < 3:
            continue
        key = _normalise_key(name)
        if key and key not in seen:
            seen.add(key)
            unique.append(_normalise(name))
    return unique


@lru_cache(maxsize=1)
def _medicine_key_map() -> Dict[str, str]:
    return {_normalise_key(name): name for name in _medicine_lexicon()}


def _known_medicines_from_line(
    line: str,
    form: Optional[str],
    dosage: Optional[str],
) -> List[Dict[str, Optional[str]]]:
    found: List[Dict[str, Optional[str]]] = []
    line_key = _normalise_key(line)
    if not line_key:
        return found

    for key, name in _medicine_key_map().items():
        if len(key) < 4:
            continue
        if key in line_key:
            found.append(
                {
                    "name": name,
                    "form": form,
                    "dosage": _nearest_dosage(line, name.split()[0]) or dosage,
                    "source_line": line,
                    "confidence": "db-exact",
                }
            )
    return found


def _correct_to_known_medicine(token: str, require_strong: bool = True) -> Optional[tuple[str, int]]:
    token_key = _normalise_key(token)
    if not token_key or len(token_key) < 3:
        return None

    exact = _medicine_key_map().get(token_key)
    if exact:
        return exact, 100

    try:
        from rapidfuzz import fuzz, process  # type: ignore

        choices = _medicine_lexicon()
        cutoff = 88 if require_strong else 80
        match = process.extractOne(token, choices, scorer=fuzz.WRatio, score_cutoff=cutoff)
        if not match:
            return _correct_to_web_medicine(token)
        name, score, _ = match
        return name, int(score)
    except Exception:
        return _correct_to_web_medicine(token)


@lru_cache(maxsize=512)
def _correct_to_web_medicine(token: str) -> Optional[tuple[str, int]]:
    web = lookup_web_medicine(token, timeout=2.5)
    if not web:
        return None
    return web.name, 70


def _extract_form(line: str) -> Optional[str]:
    match = _FORM_PATTERN.search(line)
    if not match:
        return None
    value = match.group(1).lower()
    mapping = {
        "tab": "Tablet",
        "tabs": "Tablet",
        "tablet": "Tablet",
        "tablets": "Tablet",
        "cap": "Capsule",
        "caps": "Capsule",
        "capsule": "Capsule",
        "capsules": "Capsule",
        "syp": "Syrup",
        "syr": "Syrup",
        "syrup": "Syrup",
        "inj": "Injection",
        "injection": "Injection",
        "susp": "Suspension",
        "suspension": "Suspension",
        "sol": "Solution",
        "solution": "Solution",
        "oint": "Ointment",
        "ointment": "Ointment",
        "drop": "Drops",
        "drops": "Drops",
        "respule": "Respules",
        "respules": "Respules",
        "neb": "Nebulizer",
        "nebulizer": "Nebulizer",
    }
    return mapping.get(value, value.title())


def _extract_dosage(line: str) -> Optional[str]:
    match = _DOSAGE_PATTERN.search(line)
    return re.sub(r"\s+", "", match.group(0)) if match else None


def _nearest_dosage(line: str, token: str) -> Optional[str]:
    token_match = re.search(re.escape(token), line, flags=re.IGNORECASE)
    if not token_match:
        return None
    best = None
    best_distance = 10**9
    for match in _DOSAGE_PATTERN.finditer(line):
        distance = abs(match.start() - token_match.end())
        if distance < best_distance:
            best = match.group(0)
            best_distance = distance
    return re.sub(r"\s+", "", best) if best else None


def _fallback_medicine_from_line(
    line: str,
    form: Optional[str],
    dosage: Optional[str],
) -> Optional[Dict[str, Optional[str]]]:
    """Extract a brand phrase from a medicine-looking line, even if not in CSV."""
    working = re.sub(r"^\s*(?:rx|r/|\d+[\).:-]?|[-*])\s*", " ", line, flags=re.I)

    form_match = _FORM_PATTERN.search(working)
    if form_match:
        working = working[form_match.end() :]
    else:
        working = _BEFORE_KW.sub(" ", working, count=1)

    cut_points = [len(working)]
    for pattern in (_DOSAGE_PATTERN, _FREQUENCY_PATTERN):
        match = pattern.search(working)
        if match:
            cut_points.append(match.start())

    for marker in (" - ", " : ", " ; ", ","):
        pos = working.find(marker)
        if pos > 0:
            cut_points.append(pos)

    phrase = working[: min(cut_points)]
    phrase = re.sub(r"\([^)]*\)", " ", phrase)
    phrase = re.sub(r"[^A-Za-z0-9+ -]+", " ", phrase)
    raw_tokens = _PHRASE_TOKEN.findall(phrase)
    tokens = [
        token
        for index, token in enumerate(raw_tokens)
        if _is_phrase_token(token, is_first=index == 0)
    ]

    while tokens and tokens[-1].lower() in {"ml", "mg", "iu", "unit", "units"}:
        tokens.pop()

    if not tokens:
        return None

    tokens = tokens[:4]
    name = _normalise(" ".join(tokens))
    if len(_normalise_key(name)) < 3:
        return None

    corrected = _correct_to_known_medicine(name, require_strong=True)
    if corrected:
        name, score = corrected
        confidence = "db-exact" if score == 100 else f"db-fuzzy-{score}"
    else:
        confidence = "ocr-context"

    return {
        "name": name,
        "form": form,
        "dosage": _nearest_dosage(line, tokens[0]) or dosage,
        "source_line": line,
        "confidence": confidence,
    }


def _is_candidate(token: str) -> bool:
    token = token.strip()
    if not _MEDICINE_CANDIDATE.match(token):
        return False
    if _BAD_TOKEN_PATTERN.match(token):
        return False
    return not token.isdigit()


def _is_phrase_token(token: str, is_first: bool = False) -> bool:
    token = token.strip()
    if _BAD_TOKEN_PATTERN.match(token) or token.isdigit():
        return False
    if is_first:
        return bool(_MEDICINE_CANDIDATE.match(token))
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9+-]{1,34}$", token))


def _normalise_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _dedupe_details(items: List[Dict[str, Optional[str]]]) -> List[Dict[str, Optional[str]]]:
    seen: set[str] = set()
    unique: List[Dict[str, Optional[str]]] = []
    for item in items:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue

        compact_key = _normalise_key(name)
        source_line = str(item.get("source_line") or "")
        replaced = False
        skip = False
        for index, existing in enumerate(unique):
            existing_name = str(existing.get("name") or "")
            existing_key = _normalise_key(existing_name)
            same_line = source_line and source_line == str(existing.get("source_line") or "")
            if not same_line or not compact_key or not existing_key:
                continue
            if existing_key in compact_key and len(compact_key) > len(existing_key):
                seen.discard(existing_name.lower())
                unique[index] = item
                seen.add(key)
                replaced = True
                break
            if compact_key in existing_key:
                skip = True
                break
        if replaced or skip:
            continue

        seen.add(key)
        unique.append(item)
    return unique


def _normalise(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).title()


def _blank_to_none(value) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _json_slice(content: str) -> str:
    start = content.find("[")
    end = content.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return "[]"
    return content[start : end + 1]
