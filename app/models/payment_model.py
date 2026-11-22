"""Demo payment ledger persistence helpers."""
from __future__ import annotations

from app.extensions import execute, query_all, query_one


def record_payment(invoice_id: int, utr: str, method: str, amount: float) -> int:
    cursor = execute(
        """INSERT INTO payments (invoice_id, utr, method, amount, status)
           VALUES (?, ?, ?, ?, 'SUCCESS')""",
        (invoice_id, utr, method, amount),
    )
    return cursor.lastrowid


def get_payment_by_utr(utr: str):
    return query_one(
        """SELECT p.*, i.invoice_no, i.client_name, i.grand_total, i.currency
           FROM payments p JOIN invoices i ON i.id = p.invoice_id
           WHERE p.utr = ?""",
        (utr,),
    )


def list_payments(limit: int = 50):
    return query_all(
        """SELECT p.*, i.invoice_no, i.client_name FROM payments p
           JOIN invoices i ON i.id = p.invoice_id
           ORDER BY p.id DESC LIMIT ?""",
        (limit,),
    )
