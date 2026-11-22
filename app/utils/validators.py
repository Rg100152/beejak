"""Lightweight input validators used by the Beejak routes and tests."""
from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_UPI_RE = re.compile(r"^[A-Za-z0-9._\-]+@[A-Za-z0-9.\-]+$")
_GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")


def is_valid_email(value: str) -> bool:
    return bool(value) and bool(_EMAIL_RE.match(value.strip()))


def is_valid_upi_id(value: str) -> bool:
    return bool(value) and bool(_UPI_RE.match(value.strip()))


def is_valid_gstin(value: str) -> bool:
    return bool(value) and bool(_GSTIN_RE.match(value.strip().upper()))


def clean_text(value, limit: int = 500) -> str:
    """Strip control characters and trim user supplied text."""
    text = str(value or "").strip()
    text = "".join(char for char in text if char >= " " or char in "\n\t")
    return text[:limit]


def as_float(value, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if number == number and abs(number) != float("inf") else default
