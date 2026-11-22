"""Public client checkout and payment receipt pages."""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, url_for

from app.models.invoice_model import get_invoice_bundle
from app.models.payment_model import get_payment_by_utr
from app.services.upi_qr_service import upi_metadata
from app.utils.formatters import amount_in_words

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/pay/<int:invoice_id>")
def checkout(invoice_id: int):
    invoice = get_invoice_bundle(invoice_id)
    if invoice is None:
        flash("Invoice not found.", "error")
        return redirect(url_for("dashboard.index"))
    return render_template(
        "payments/checkout.html",
        invoice=invoice,
        upi=upi_metadata(
            invoice["upi_id"], invoice["grand_total"],
            invoice["invoice_no"], invoice["currency"],
        ),
        amount_words=amount_in_words(invoice["grand_total"]),
        active_nav="payments",
    )


@payments_bp.route("/receipt/<utr>")
def receipt(utr: str):
    payment = get_payment_by_utr(utr)
    if payment is None:
        flash("Receipt not found.", "error")
        return redirect(url_for("dashboard.index"))
    invoice = get_invoice_bundle(payment["invoice_id"])
    return render_template(
        "payments/receipt.html",
        payment=dict(payment),
        invoice=invoice,
        active_nav="payments",
    )
