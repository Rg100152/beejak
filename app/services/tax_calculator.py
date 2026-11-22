"""Pure GST / tax calculation engine (no database or Flask dependencies)."""
from __future__ import annotations

from app.utils.validators import as_float


def round2(value: float) -> float:
    return round(value + 1e-9, 2)


def line_total(qty, unit_price) -> float:
    return round2(as_float(qty) * as_float(unit_price))


def calculate_totals(items, discount_pct=0, tax_pct=0, tax_mode="CGST_SGST") -> dict:
    """Compute subtotal, discount, CGST/SGST or IGST split and grand total.

    ``items`` is an iterable of dicts with ``qty`` and ``unit_price`` keys
    (or simple numeric strings).  All money values are rounded to 2 decimals.
    """
    subtotal = 0.0
    normalised = []
    for raw in items or []:
        qty = as_float(raw.get("qty", 0)) if isinstance(raw, dict) else as_float(raw)
        price = as_float(raw.get("unit_price", 0)) if isinstance(raw, dict) else 0.0
        total = line_total(qty, price)
        subtotal = round2(subtotal + total)
        entry = dict(raw) if isinstance(raw, dict) else {"qty": qty, "unit_price": price}
        entry["line_total"] = total
        normalised.append(entry)

    discount = round2(subtotal * as_float(discount_pct) / 100.0)
    taxable = round2(max(0.0, subtotal - discount))
    tax_amount = round2(taxable * as_float(tax_pct) / 100.0)

    if str(tax_mode).upper() == "IGST":
        cgst = 0.0
        sgst = 0.0
        igst = tax_amount
    else:
        cgst = round2(tax_amount / 2.0)
        sgst = round2(tax_amount - cgst)
        igst = 0.0

    return {
        "items": normalised,
        "subtotal": subtotal,
        "discount_pct": as_float(discount_pct),
        "discount_amount": discount,
        "taxable_amount": taxable,
        "tax_pct": as_float(tax_pct),
        "tax_mode": "IGST" if str(tax_mode).upper() == "IGST" else "CGST_SGST",
        "cgst": cgst,
        "sgst": sgst,
        "igst": igst,
        "tax_amount": tax_amount,
        "grand_total": round2(taxable + tax_amount),
    }
