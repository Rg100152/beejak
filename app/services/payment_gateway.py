"""Beejak Pay Sandbox — deterministic helpers for the demo payment flow.

This is a *simulation*: no real money moves and no external payment API is
contacted.  The generated UTR mirrors the format used by Indian UPI receipts.
"""
from __future__ import annotations

import secrets
from datetime import datetime

SUPPORTED_METHODS = {
    "UPI": "UPI Instant Pay",
    "CARD": "Test Card •••• 4242",
    "NETBANKING": "NetBanking (Sandbox)",
}


def generate_utr(year: int | None = None) -> str:
    """Generate a unique-looking demo UTR, e.g. UTR202684512097."""
    year = year or datetime.now().year
    return f"UTR{year}{secrets.randbelow(900_000_000) + 100_000_000:09d}"


def simulate_payment(method: str = "UPI", amount: float = 0) -> dict:
    """Return a successful sandbox payment envelope."""
    key = str(method or "UPI").upper()
    return {
        "status": "SUCCESS",
        "method": key if key in SUPPORTED_METHODS else "UPI",
        "method_label": SUPPORTED_METHODS.get(key, SUPPORTED_METHODS["UPI"]),
        "amount": round(float(amount or 0), 2),
        "utr": generate_utr(),
        "paid_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
    }
