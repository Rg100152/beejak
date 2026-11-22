"""Client directory persistence helpers."""
from __future__ import annotations

from app.extensions import execute, query_all, query_one


def list_clients():
    return query_all(
        """SELECT c.*,
                  COUNT(i.id) AS invoice_count,
                  COALESCE(SUM(i.grand_total), 0) AS billed_total
           FROM clients c
           LEFT JOIN invoices i ON i.client_id = c.id
           GROUP BY c.id
           ORDER BY c.name COLLATE NOCASE"""
    )


def get_client(client_id: int):
    return query_one("SELECT * FROM clients WHERE id = ?", (client_id,))


def create_client(data: dict) -> int:
    cursor = execute(
        """INSERT INTO clients (name, company, email, gstin, city)
           VALUES (?, ?, ?, ?, ?)""",
        (
            data.get("name", "").strip(),
            data.get("company", "").strip(),
            data.get("email", "").strip(),
            data.get("gstin", "").strip().upper(),
            data.get("city", "").strip(),
        ),
    )
    return cursor.lastrowid


def client_invoices(client_id: int):
    return query_all(
        "SELECT * FROM invoices WHERE client_id = ? ORDER BY issue_date DESC",
        (client_id,),
    )
