"""NPCI UPI payment URI builder and QR metadata helpers."""
from __future__ import annotations

from urllib.parse import quote

from config import PAYEE_NAME, UPI_APPS


def build_upi_uri(
    upi_id: str,
    amount=0,
    currency: str = "INR",
    note: str = "",
    payee_name: str = PAYEE_NAME,
) -> str:
    """Build a standard ``upi://pay`` deep link with pre-filled amount.

    Example::

        upi://pay?pa=rajgautam@upi&pn=Raj%20Gautam&am=15000.00&cu=INR&tn=BJK-2026-104
    """
    try:
        value = float(amount or 0)
    except (TypeError, ValueError):
        value = 0.0
    params = (
        ("pa", str(upi_id or "").strip()),
        ("pn", payee_name),
        ("am", f"{value:.2f}"),
        ("cu", currency or "INR"),
        ("tn", note or ""),
    )
    return "upi://pay?" + "&".join(
        f"{key}={quote(str(val), safe='')}" for key, val in params
    )


def upi_metadata(upi_id: str, amount=0, invoice_no: str = "", currency: str = "INR") -> dict:
    """Return everything the template / JS needs for the Scan & Pay box."""
    uri = build_upi_uri(upi_id, amount, currency, invoice_no)
    return {
        "uri": uri,
        "upi_id": upi_id,
        "amount": amount,
        "currency": currency,
        "invoice_no": invoice_no,
        "apps": list(UPI_APPS),
    }
