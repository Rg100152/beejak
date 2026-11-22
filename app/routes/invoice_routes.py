"""Invoice builder, print view and status routes."""
from __future__ import annotations

import json
from datetime import date, timedelta

from flask import (
    Blueprint, flash, jsonify, redirect, render_template, request, url_for,
)

from app.models.client_model import list_clients
from app.models.invoice_model import (
    get_invoice_bundle, next_invoice_no, set_status, create_invoice, update_invoice,
)
from app.services.upi_qr_service import upi_metadata
from config import DEFAULT_TAX_MODE, DEFAULT_UPI_ID, STATUSES
from app.utils.formatters import amount_in_words

invoices_bp = Blueprint("invoices", __name__)


def _form_payload() -> dict:
    """Normalise the builder form (line items arrive as a JSON string)."""
    try:
        items = json.loads(request.form.get("items", "[]"))
    except (TypeError, ValueError):
        items = []
    if not isinstance(items, list):
        items = []
    return {
        "invoice_no": request.form.get("invoice_no", "").strip(),
        "client_id": request.form.get("client_id") or None,
        "client_name": request.form.get("client_name", "").strip(),
        "client_company": request.form.get("client_company", "").strip(),
        "client_email": request.form.get("client_email", "").strip(),
        "issue_date": request.form.get("issue_date") or date.today().isoformat(),
        "due_date": request.form.get("due_date") or date.today().isoformat(),
        "currency": request.form.get("currency", "INR"),
        "status": request.form.get("status", "DRAFT"),
        "accent": request.form.get("accent", "emerald"),
        "upi_id": request.form.get("upi_id", DEFAULT_UPI_ID).strip(),
        "tax_mode": request.form.get("tax_mode", DEFAULT_TAX_MODE),
        "notes": request.form.get("notes", "").strip(),
        "discount_pct": request.form.get("discount_pct", 0),
        "tax_pct": request.form.get("tax_pct", 0),
        "items": items,
    }


def _paper_context(invoice: dict) -> dict:
    return {
        "upi": upi_metadata(
            invoice.get("upi_id", DEFAULT_UPI_ID),
            invoice.get("grand_total", 0),
            invoice.get("invoice_no", ""),
            invoice.get("currency", "INR"),
        ),
        "amount_words": amount_in_words(invoice.get("grand_total", 0)),
    }


@invoices_bp.route("/invoices/create")
def create():
    today = date.today()
    draft = {
        "invoice_no": next_invoice_no(),
        "client_name": "",
        "client_company": "",
        "client_email": "",
        "client_gstin": "",
        "issue_date": today.isoformat(),
        "due_date": (today + timedelta(days=14)).isoformat(),
        "currency": "INR",
        "status": "DRAFT",
        "accent": "emerald",
        "upi_id": DEFAULT_UPI_ID,
        "tax_mode": DEFAULT_TAX_MODE,
        "notes": "Thank you for choosing Beejak. Payment is appreciated within the due date.",
        "discount_pct": 0,
        "tax_pct": 18,
        "subtotal": 0,
        "discount_amount": 0,
        "tax_amount": 0,
        "grand_total": 0,
        "items": [{"description": "", "qty": 1, "unit_price": 0, "line_total": 0}],
    }
    return render_template(
        "invoices/builder.html",
        invoice=draft,
        invoice_id=None,
        clients=list_clients(),
        is_new=True,
        active_nav="invoices",
        **_paper_context(draft),
    )


@invoices_bp.route("/invoices/<int:invoice_id>/edit")
def edit(invoice_id: int):
    invoice = get_invoice_bundle(invoice_id)
    if invoice is None:
        flash("Invoice not found.", "error")
        return redirect(url_for("dashboard.index"))
    if not invoice.get("items"):
        invoice["items"] = [{"description": "", "qty": 1, "unit_price": 0}]
    return render_template(
        "invoices/builder.html",
        invoice=invoice,
        invoice_id=invoice_id,
        clients=list_clients(),
        is_new=False,
        active_nav="invoices",
        **_paper_context(invoice),
    )


@invoices_bp.route("/invoices", methods=["POST"])
def store():
    payload = _form_payload()
    if not payload["client_name"]:
        flash("Client name is required.", "error")
        return redirect(url_for("invoices.create"))
    invoice_id = create_invoice(payload)
    flash(f"Invoice {payload['invoice_no']} saved successfully.", "success")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True, "id": invoice_id, "invoice_no": payload["invoice_no"]})
    return redirect(url_for("invoices.edit", invoice_id=invoice_id))


@invoices_bp.route("/invoices/<int:invoice_id>/update", methods=["POST"])
def update(invoice_id: int):
    payload = _form_payload()
    if get_invoice_bundle(invoice_id) is None:
        flash("Invoice not found.", "error")
        return redirect(url_for("dashboard.index"))
    update_invoice(invoice_id, payload)
    flash("Invoice updated — live preview is in sync.", "success")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True, "id": invoice_id})
    return redirect(url_for("invoices.edit", invoice_id=invoice_id))


@invoices_bp.route("/invoices/<int:invoice_id>")
def print_view(invoice_id: int):
    invoice = get_invoice_bundle(invoice_id)
    if invoice is None:
        flash("Invoice not found.", "error")
        return redirect(url_for("dashboard.index"))
    return render_template(
        "invoices/print_view.html",
        invoice=invoice,
        active_nav="invoices",
        **_paper_context(invoice),
    )


@invoices_bp.route("/invoices/<int:invoice_id>/status", methods=["POST"])
def change_status(invoice_id: int):
    status = request.form.get("status", "").upper()
    if status in STATUSES:
        set_status(invoice_id, status)
        flash(f"Invoice marked {status}.", "success")
    else:
        flash("Invalid status.", "error")
    return redirect(request.referrer or url_for("dashboard.index"))


@invoices_bp.route("/invoices/<int:invoice_id>/send", methods=["POST"])
def mark_sent(invoice_id: int):
    set_status(invoice_id, "SENT")
    flash("Invoice marked as SENT to client.", "success")
    return redirect(request.referrer or url_for("dashboard.index"))
