"""Invoice and line-item persistence helpers."""
from __future__ import annotations

from datetime import date

from app.extensions import execute, query_all, query_one
from app.services.tax_calculator import calculate_totals, line_total
from config import DEFAULT_ACCENT, DEFAULT_TAX_MODE, DEFAULT_UPI_ID


INVOICE_COLUMNS = (
    "invoice_no", "client_id", "client_name", "client_company", "client_email",
    "issue_date", "due_date", "currency", "status", "accent", "upi_id",
    "tax_mode", "notes", "discount_pct", "tax_pct", "subtotal",
    "discount_amount", "tax_amount", "grand_total", "utr",
)


def next_invoice_no() -> str:
    """Return the next sequential number, e.g. BJK-2026-104."""
    year = date.today().year
    prefix = f"BJK-{year}-"
    row = query_one(
        "SELECT invoice_no FROM invoices WHERE invoice_no LIKE ? "
        "ORDER BY invoice_no DESC LIMIT 1",
        (prefix + "%",),
    )
    sequence = 103
    if row:
        try:
            sequence = int(str(row["invoice_no"]).rsplit("-", 1)[-1])
        except ValueError:
            pass
    return f"{prefix}{sequence + 1:03d}"


def list_invoices(status: str = "", search: str = ""):
    sql = """SELECT i.*, c.gstin AS client_gstin
             FROM invoices i LEFT JOIN clients c ON c.id = i.client_id
             WHERE 1 = 1"""
    params = []
    if status and status.upper() in {"DRAFT", "SENT", "PAID", "OVERDUE"}:
        sql += " AND i.status = ?"
        params.append(status.upper())
    if search:
        sql += " AND (i.invoice_no LIKE ? OR i.client_name LIKE ? OR i.client_company LIKE ?)"
        needle = f"%{search}%"
        params.extend([needle, needle, needle])
    sql += " ORDER BY i.issue_date DESC, i.id DESC"
    return query_all(sql, tuple(params))


def get_invoice(invoice_id: int):
    return query_one(
        """SELECT i.*, c.gstin AS client_gstin, c.city AS client_city
           FROM invoices i LEFT JOIN clients c ON c.id = i.client_id
           WHERE i.id = ?""",
        (invoice_id,),
    )


def get_invoice_items(invoice_id: int):
    return query_all(
        "SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY sort_order, id",
        (invoice_id,),
    )


def get_invoice_bundle(invoice_id: int) -> dict | None:
    invoice = get_invoice(invoice_id)
    if invoice is None:
        return None
    result = dict(invoice)
    result["items"] = [dict(item) for item in get_invoice_items(invoice_id)]
    return result


def _save_items(invoice_id: int, items: list[dict]) -> None:
    execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
    for index, item in enumerate(items):
        description = str(item.get("description", "")).strip() or "Service"
        qty = float(item.get("qty") or 0)
        price = float(item.get("unit_price") or 0)
        execute(
            """INSERT INTO invoice_items
               (invoice_id, description, qty, unit_price, line_total, sort_order)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (invoice_id, description, qty, price, line_total(qty, price), index),
        )


def create_invoice(data: dict) -> int:
    """Create an invoice together with its line items."""
    items = data.get("items") or []
    totals = calculate_totals(
        items, data.get("discount_pct", 0), data.get("tax_pct", 0),
        data.get("tax_mode", DEFAULT_TAX_MODE),
    )
    values = {
        "invoice_no": data.get("invoice_no") or next_invoice_no(),
        "client_id": data.get("client_id") or None,
        "client_name": data.get("client_name", "").strip(),
        "client_company": data.get("client_company", "").strip(),
        "client_email": data.get("client_email", "").strip(),
        "issue_date": data.get("issue_date") or date.today().isoformat(),
        "due_date": data.get("due_date") or date.today().isoformat(),
        "currency": data.get("currency") or "INR",
        "status": data.get("status") or "DRAFT",
        "accent": data.get("accent") or DEFAULT_ACCENT,
        "upi_id": data.get("upi_id") or DEFAULT_UPI_ID,
        "tax_mode": data.get("tax_mode") or DEFAULT_TAX_MODE,
        "notes": data.get("notes", "").strip(),
        "discount_pct": float(data.get("discount_pct") or 0),
        "tax_pct": float(data.get("tax_pct") or 0),
        "subtotal": totals["subtotal"],
        "discount_amount": totals["discount_amount"],
        "tax_amount": totals["tax_amount"],
        "grand_total": totals["grand_total"],
        "utr": "",
    }
    cursor = execute(
        f"INSERT INTO invoices ({', '.join(INVOICE_COLUMNS)}) "
        f"VALUES ({', '.join('?' for _ in INVOICE_COLUMNS)})",
        tuple(values[key] for key in INVOICE_COLUMNS),
    )
    invoice_id = cursor.lastrowid
    _save_items(invoice_id, totals["items"])
    return invoice_id


def update_invoice(invoice_id: int, data: dict) -> None:
    items = data.get("items") or []
    totals = calculate_totals(
        items, data.get("discount_pct", 0), data.get("tax_pct", 0),
        data.get("tax_mode", DEFAULT_TAX_MODE),
    )
    existing = get_invoice(invoice_id)
    values = {
        "invoice_no": data.get("invoice_no") or existing["invoice_no"],
        "client_id": data.get("client_id") or None,
        "client_name": data.get("client_name", "").strip(),
        "client_company": data.get("client_company", "").strip(),
        "client_email": data.get("client_email", "").strip(),
        "issue_date": data.get("issue_date") or existing["issue_date"],
        "due_date": data.get("due_date") or existing["due_date"],
        "currency": data.get("currency") or existing["currency"],
        "status": data.get("status") or existing["status"],
        "accent": data.get("accent") or existing["accent"],
        "upi_id": data.get("upi_id") or existing["upi_id"],
        "tax_mode": data.get("tax_mode") or existing["tax_mode"],
        "notes": data.get("notes", "").strip(),
        "discount_pct": float(data.get("discount_pct") or 0),
        "tax_pct": float(data.get("tax_pct") or 0),
        "subtotal": totals["subtotal"],
        "discount_amount": totals["discount_amount"],
        "tax_amount": totals["tax_amount"],
        "grand_total": totals["grand_total"],
        "utr": existing["utr"],
    }
    assignments = ", ".join(f"{key} = ?" for key in INVOICE_COLUMNS)
    execute(
        f"UPDATE invoices SET {assignments}, updated_at = datetime('now') WHERE id = ?",
        tuple([values[key] for key in INVOICE_COLUMNS] + [invoice_id]),
    )
    _save_items(invoice_id, totals["items"])


def set_status(invoice_id: int, status: str) -> None:
    execute(
        "UPDATE invoices SET status = ?, updated_at = datetime('now') WHERE id = ?",
        (status.upper(), invoice_id),
    )


def mark_paid(invoice_id: int, utr: str) -> None:
    execute(
        "UPDATE invoices SET status='PAID', utr=?, updated_at=datetime('now') WHERE id=?",
        (utr, invoice_id),
    )


def delete_invoice(invoice_id: int) -> None:
    execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
