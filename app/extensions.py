"""SQLite connection helpers and schema bootstrap for Beejak."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import current_app, g

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS clients (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    company     TEXT NOT NULL DEFAULT '',
    email       TEXT NOT NULL DEFAULT '',
    gstin       TEXT NOT NULL DEFAULT '',
    city        TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS invoices (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no      TEXT NOT NULL UNIQUE,
    client_id       INTEGER REFERENCES clients(id) ON DELETE SET NULL,
    client_name     TEXT NOT NULL,
    client_company  TEXT NOT NULL DEFAULT '',
    client_email    TEXT NOT NULL DEFAULT '',
    issue_date      TEXT NOT NULL,
    due_date        TEXT NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'INR',
    status          TEXT NOT NULL DEFAULT 'DRAFT',
    accent          TEXT NOT NULL DEFAULT 'emerald',
    upi_id          TEXT NOT NULL DEFAULT 'rajgautam@upi',
    tax_mode        TEXT NOT NULL DEFAULT 'CGST_SGST',
    notes           TEXT NOT NULL DEFAULT '',
    discount_pct    REAL NOT NULL DEFAULT 0,
    tax_pct         REAL NOT NULL DEFAULT 18,
    subtotal        REAL NOT NULL DEFAULT 0,
    discount_amount REAL NOT NULL DEFAULT 0,
    tax_amount      REAL NOT NULL DEFAULT 0,
    grand_total     REAL NOT NULL DEFAULT 0,
    utr             TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id  INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    qty         REAL NOT NULL DEFAULT 1,
    unit_price  REAL NOT NULL DEFAULT 0,
    line_total  REAL NOT NULL DEFAULT 0,
    sort_order  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS payments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id  INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    utr         TEXT NOT NULL UNIQUE,
    method      TEXT NOT NULL DEFAULT 'UPI',
    amount      REAL NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'SUCCESS',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_invoices_status  ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_due     ON invoices(due_date);
CREATE INDEX IF NOT EXISTS idx_items_invoice    ON invoice_items(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id);
"""


def get_db() -> sqlite3.Connection:
    """Return the request-scoped SQLite connection."""
    if "db" not in g:
        db_path = current_app.config["DATABASE"]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def close_db(_error=None) -> None:
    """Close the connection at the end of a request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Create all tables if they do not exist yet."""
    db_path = current_app.config["DATABASE"]
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA)
        connection.commit()
    finally:
        connection.close()


def init_app(app) -> None:
    """Register database lifecycle hooks on the Flask app."""
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()


def query_all(sql: str, params=()) -> list[sqlite3.Row]:
    return get_db().execute(sql, params).fetchall()


def query_one(sql: str, params=()):
    return get_db().execute(sql, params).fetchone()


def execute(sql: str, params=()):
    db = get_db()
    cursor = db.execute(sql, params)
    db.commit()
    return cursor
