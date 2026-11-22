"""CSV / JSON accounting export helpers."""
from __future__ import annotations

import csv
import io
import json


CSV_COLUMNS = [
    "invoice_no", "client_name", "client_company", "client_email",
    "issue_date", "due_date", "currency", "status", "subtotal",
    "discount_amount", "tax_pct", "tax_amount", "grand_total", "utr",
]


def invoices_to_csv(invoices) -> str:
    """Serialize invoice rows to a UTF-8 CSV string."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for invoice in invoices:
        row = dict(invoice)
        writer.writerow({key: row.get(key, "") for key in CSV_COLUMNS})
    return output.getvalue()


def invoices_to_json(invoices) -> str:
    payload = []
    for invoice in invoices:
        payload.append({key: dict(invoice).get(key) for key in CSV_COLUMNS})
    return json.dumps(payload, indent=2, ensure_ascii=False)
