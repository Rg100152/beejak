"""REST-ish JSON APIs: live tax calc, payment simulation and exports."""
from __future__ import annotations

from flask import Blueprint, Response, jsonify, request

from app.models.client_model import create_client as add_client
from app.models.invoice_model import (
    create_invoice, get_invoice, list_invoices, mark_paid, set_status,
)
from app.models.payment_model import get_payment_by_utr, record_payment
from app.services.export_service import invoices_to_csv, invoices_to_json
from app.services.payment_gateway import simulate_payment
from app.services.tax_calculator import calculate_totals
from app.services.upi_qr_service import build_upi_uri
from config import DEFAULT_UPI_ID

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.post("/calculate")
def calculate():
    payload = request.get_json(silent=True) or {}
    result = calculate_totals(
        payload.get("items", []),
        payload.get("discount_pct", 0),
        payload.get("tax_pct", 0),
        payload.get("tax_mode", "CGST_SGST"),
    )
    return jsonify(result)


@api_bp.get("/upi-uri")
def upi_uri():
    args = request.args
    return jsonify({
        "uri": build_upi_uri(
            args.get("upi_id", DEFAULT_UPI_ID),
            args.get("amount", 0),
            args.get("currency", "INR"),
            args.get("note", ""),
        )
    })


@api_bp.get("/invoices")
def invoices():
    return jsonify({"invoices": [dict(row) for row in list_invoices(
        request.args.get("status", ""), request.args.get("q", "")
    )]})


@api_bp.post("/invoices")
def create_invoice_api():
    payload = request.get_json(silent=True) or {}
    if not str(payload.get("client_name", "")).strip():
        return jsonify({"ok": False, "error": "client_name is required"}), 400
    invoice_id = create_invoice(payload)
    return jsonify({"ok": True, "id": invoice_id}), 201


@api_bp.post("/invoices/<int:invoice_id>/status")
def change_status(invoice_id: int):
    status = str((request.get_json(silent=True) or {}).get("status", "")).upper()
    if status not in {"DRAFT", "SENT", "PAID", "OVERDUE"}:
        return jsonify({"ok": False, "error": "invalid status"}), 400
    set_status(invoice_id, status)
    return jsonify({"ok": True, "status": status})


@api_bp.post("/pay/<int:invoice_id>")
def pay(invoice_id: int):
    """Complete a demo payment and sync the invoice to PAID."""
    invoice = get_invoice(invoice_id)
    if invoice is None:
        return jsonify({"ok": False, "error": "invoice not found"}), 404
    if invoice["status"] == "PAID" and invoice["utr"]:
        existing = get_payment_by_utr(invoice["utr"])
        return jsonify({
            "ok": True, "already_paid": True, "utr": invoice["utr"],
            "method": existing["method"] if existing else "UPI",
            "receipt_url": f"/receipt/{invoice['utr']}",
        })

    payload = request.get_json(silent=True) or {}
    result = simulate_payment(
        payload.get("method", "UPI"),
        payload.get("amount", invoice["grand_total"]),
    )
    record_payment(invoice_id, result["utr"], result["method"], result["amount"])
    mark_paid(invoice_id, result["utr"])
    return jsonify({
        "ok": True,
        "utr": result["utr"],
        "method": result["method"],
        "method_label": result["method_label"],
        "amount": result["amount"],
        "paid_at": result["paid_at"],
        "status": "PAID",
        "receipt_url": f"/receipt/{result['utr']}",
    })


@api_bp.get("/export/csv")
def export_csv():
    rows = list_invoices(request.args.get("status", ""), request.args.get("q", ""))
    return Response(
        invoices_to_csv(rows),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=beejak-invoices.csv"},
    )


@api_bp.get("/export/json")
def export_json():
    rows = list_invoices(request.args.get("status", ""), request.args.get("q", ""))
    return Response(
        invoices_to_json(rows),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=beejak-invoices.json"},
    )


@api_bp.post("/clients")
def create_client_api():
    payload = request.get_json(silent=True) or {}
    if not str(payload.get("name", "")).strip():
        return jsonify({"ok": False, "error": "name is required"}), 400
    return jsonify({"ok": True, "id": add_client(payload)}), 201
