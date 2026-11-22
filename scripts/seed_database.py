#!/usr/bin/env python3
"""Seed Beejak with six realistic Indian client invoices and demo payments.

    python3 scripts/seed_database.py
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.extensions import execute, get_db  # noqa: E402
from app.services.tax_calculator import calculate_totals  # noqa: E402
from config import DEFAULT_UPI_ID  # noqa: E402

TODAY = date.today()
YEAR = TODAY.year
PREFIX = f"BJK-{YEAR}-"

CLIENTS = [
    ("Aarav Infotech", "Aarav Infotech Pvt Ltd", "billing@aaravinfotech.in", "09AABCA1234K1ZP", "Noida, UP"),
    ("Shri Ganesh Traders", "Shri Ganesh Traders", "accounts@ganeshtraders.in", "09AABCS5678L1ZQ", "Jaunpur, UP"),
    ("Varanasi Tech Labs", "Varanasi Tech Labs LLP", "hello@varanasitech.in", "09AABCV9012M1ZR", "Varanasi, UP"),
    ("Lucknow Creative Studio", "Lucknow Creative Studio", "finance@lucknowcreative.in", "09AABCL3456N1ZS", "Lucknow, UP"),
    ("Kanpur Logistics Co.", "Kanpur Logistics Company", "admin@kanplogistics.in", "09AABCK7890P1ZT", "Kanpur, UP"),
    ("Priya Manchanda", "Priya Manchanda Designs", "priya@manchandadesigns.in", "07AABCP2345Q1ZU", "New Delhi, DL"),
]

INVOICES = [
    {
        "no": f"{PREFIX}101", "client": 0, "status": "PAID", "currency": "INR",
        "issue": TODAY - timedelta(days=38), "due": TODAY - timedelta(days=8),
        "tax": 18, "discount": 0, "accent": "emerald", "utr": f"UTR{YEAR}112045561",
        "notes": "Website design & development — Phase 1 complete. Thank you!",
        "items": [
            ("UI/UX design & wireframes", 1, 32000),
            ("Frontend development (React)", 1, 58000),
            ("Deployment & QA", 1, 15000),
        ],
    },
    {
        "no": f"{PREFIX}102", "client": 1, "status": "SENT", "currency": "INR",
        "issue": TODAY - timedelta(days=14), "due": TODAY + timedelta(days=14),
        "tax": 18, "discount": 5, "accent": "navy", "utr": "",
        "notes": "Security audit report attached. Please pay via UPI QR below.",
        "items": [
            ("VAPT penetration testing", 1, 45000),
            ("Firewall configuration review", 2, 8000),
            ("Compliance report", 1, 12000),
        ],
    },
    {
        "no": f"{PREFIX}103", "client": 2, "status": "SENT", "currency": "INR",
        "issue": TODAY - timedelta(days=25), "due": TODAY + timedelta(days=4),
        "tax": 12, "discount": 0, "accent": "saffron", "utr": "",
        "notes": "REST API integration milestone 2.",
        "items": [
            ("Payment gateway API integration", 1, 36500),
            ("Webhook & retry logic", 1, 14000),
            ("API documentation", 1, 6500),
        ],
    },
    {
        "no": f"{PREFIX}104", "client": 3, "status": "DRAFT", "currency": "INR",
        "issue": TODAY, "due": TODAY + timedelta(days=20),
        "tax": 18, "discount": 10, "accent": "emerald", "utr": "",
        "notes": "Draft — awaiting final scope confirmation.",
        "items": [
            ("Brand identity system", 1, 28000),
            ("Component UI kit (Figma)", 1, 22000),
            ("Social media templates", 10, 1500),
        ],
    },
    {
        "no": f"{PREFIX}105", "client": 4, "status": "SENT", "currency": "USD",
        "issue": TODAY - timedelta(days=62), "due": TODAY - timedelta(days=21),
        "tax": 5, "discount": 0, "accent": "navy", "utr": "",
        "notes": "Overdue reminder sent. Kindly clear at the earliest.",
        "items": [
            ("Logistics dashboard setup", 1, 2400),
            ("Data pipeline configuration", 2, 750),
        ],
    },
    {
        "no": f"{PREFIX}106", "client": 5, "status": "PAID", "currency": "INR",
        "issue": TODAY - timedelta(days=9), "due": TODAY + timedelta(days=5),
        "tax": 18, "discount": 0, "accent": "saffron", "utr": f"UTR{YEAR}778912340",
        "notes": "Monthly SEO & performance retainer — paid in full.",
        "items": [
            ("Technical SEO audit", 1, 18000),
            ("Performance optimisation", 1, 24000),
            ("Monthly reporting", 1, 6000),
        ],
    },
]


def seed() -> None:
    app = create_app()
    with app.app_context():
        db = get_db()
        db.executescript(
            "DELETE FROM payments; DELETE FROM invoice_items; DELETE FROM invoices; DELETE FROM clients; "
            "DELETE FROM sqlite_sequence WHERE name IN "
            "('payments', 'invoice_items', 'invoices', 'clients');"
        )
        db.commit()

        client_ids = []
        for client in CLIENTS:
            cursor = execute(
                "INSERT INTO clients (name, company, email, gstin, city) VALUES (?, ?, ?, ?, ?)",
                client,
            )
            client_ids.append(cursor.lastrowid)

        for index, invoice in enumerate(INVOICES, start=1):
            items = [
                {"description": desc, "qty": qty, "unit_price": price}
                for desc, qty, price in invoice["items"]
            ]
            totals = calculate_totals(items, invoice["discount"], invoice["tax"])
            execute(
                """INSERT INTO invoices
                   (invoice_no, client_id, client_name, client_company, client_email,
                    issue_date, due_date, currency, status, accent, upi_id, notes,
                    discount_pct, tax_pct, subtotal, discount_amount, tax_amount,
                    grand_total, utr)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    invoice["no"], client_ids[invoice["client"]],
                    CLIENTS[invoice["client"]][0], CLIENTS[invoice["client"]][1],
                    CLIENTS[invoice["client"]][2],
                    invoice["issue"].isoformat(), invoice["due"].isoformat(),
                    invoice["currency"], invoice["status"], invoice["accent"],
                    DEFAULT_UPI_ID, invoice["notes"], invoice["discount"],
                    invoice["tax"], totals["subtotal"], totals["discount_amount"],
                    totals["tax_amount"], totals["grand_total"], invoice["utr"],
                ),
            )
            invoice_row = execute(
                "SELECT id FROM invoices WHERE invoice_no = ?", (invoice["no"],)
            ).fetchone()
            invoice_id = invoice_row["id"]
            for order, item in enumerate(totals["items"]):
                execute(
                    """INSERT INTO invoice_items
                       (invoice_id, description, qty, unit_price, line_total, sort_order)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (invoice_id, item["description"], item["qty"], item["unit_price"],
                     item["line_total"], order),
                )
            if invoice["status"] == "PAID":
                execute(
                    """INSERT INTO payments (invoice_id, utr, method, amount, status)
                       VALUES (?, ?, ?, ?, 'SUCCESS')""",
                    (invoice_id, invoice["utr"], "UPI", totals["grand_total"]),
                )
        print(f"Seeded {len(CLIENTS)} clients and {len(INVOICES)} invoices into database/beejak.db")


if __name__ == "__main__":
    seed()
