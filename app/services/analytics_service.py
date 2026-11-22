"""Revenue KPI and reporting queries for the billing dashboard."""
from __future__ import annotations

from datetime import date

from app.extensions import query_all, query_one
from app.utils.formatters import month_name


def get_kpis() -> dict:
    """Return headline metrics derived from the invoices table."""
    totals = query_one(
        """SELECT COUNT(*) AS invoice_count,
                  COALESCE(SUM(grand_total), 0) AS total_invoiced,
                  COALESCE(SUM(CASE WHEN status='PAID' THEN grand_total ELSE 0 END), 0) AS paid_revenue,
                  COALESCE(SUM(CASE WHEN status!='PAID' THEN grand_total ELSE 0 END), 0) AS pending_dues,
                  SUM(CASE WHEN status='PAID' THEN 1 ELSE 0 END) AS paid_count,
                  SUM(CASE WHEN status='SENT' THEN 1 ELSE 0 END) AS sent_count,
                  SUM(CASE WHEN status='DRAFT' THEN 1 ELSE 0 END) AS draft_count
           FROM invoices"""
    )
    today = date.today().isoformat()
    overdue = query_one(
        "SELECT COUNT(*) AS n FROM invoices WHERE due_date < ? AND status != 'PAID'",
        (today,),
    )
    return {
        "invoice_count": totals["invoice_count"],
        "total_invoiced": totals["total_invoiced"] or 0,
        "paid_revenue": totals["paid_revenue"] or 0,
        "pending_dues": totals["pending_dues"] or 0,
        "overdue_count": overdue["n"],
        "paid_count": totals["paid_count"] or 0,
        "sent_count": totals["sent_count"] or 0,
        "draft_count": totals["draft_count"] or 0,
        "collection_rate": round(
            ((totals["paid_revenue"] or 0) / (totals["total_invoiced"] or 1)) * 100, 1
        ),
    }


def monthly_revenue(months: int = 6) -> dict:
    """Return labels, billed and collected series for the last N months."""
    rows = query_all(
        """SELECT substr(issue_date, 1, 7) AS ym,
                  SUM(grand_total) AS billed,
                  SUM(CASE WHEN status='PAID' THEN grand_total ELSE 0 END) AS collected
           FROM invoices
           GROUP BY ym ORDER BY ym DESC LIMIT ?""",
        (months,),
    )
    by_month = {row["ym"]: row for row in rows}
    today = date.today()
    labels, billed, collected = [], [], []
    for offset in range(months - 1, -1, -1):
        index = today.month - offset - 1
        year = today.year
        while index < 0:
            index += 12
            year -= 1
        month = index + 1
        key = f"{year:04d}-{month:02d}"
        entry = by_month.get(key)
        labels.append(month_name(year, month))
        billed.append(round(entry["billed"] if entry else 0, 2))
        collected.append(round(entry["collected"] if entry else 0, 2))
    return {"labels": labels, "billed": billed, "collected": collected}


def status_breakdown() -> list[dict]:
    rows = query_all("SELECT status, COUNT(*) AS n FROM invoices GROUP BY status")
    return [{"status": row["status"], "count": row["n"]} for row in rows]


def aging_report() -> dict:
    """Bucket outstanding invoices by how many days past due they are."""
    rows = query_all(
        "SELECT due_date, grand_total FROM invoices WHERE status != 'PAID'"
    )
    today = date.today()
    buckets = {"current": 0.0, "1_30": 0.0, "31_60": 0.0, "60_plus": 0.0}
    for row in rows:
        try:
            due = date.fromisoformat(row["due_date"])
        except (TypeError, ValueError):
            continue
        days = (today - due).days
        key = "current" if days <= 0 else "1_30" if days <= 30 else "31_60" if days <= 60 else "60_plus"
        buckets[key] += row["grand_total"] or 0
    return {key: round(value, 2) for key, value in buckets.items()}
