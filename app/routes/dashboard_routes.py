"""Dashboard, KPI and billing ledger routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request

from app.models.invoice_model import list_invoices
from app.services.analytics_service import (
    aging_report, get_kpis, monthly_revenue, status_breakdown,
)
from config import STATUSES

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    status = request.args.get("status", "").strip().upper()
    search = request.args.get("q", "").strip()
    invoices = list_invoices(status, search)
    return render_template(
        "dashboard/index.html",
        invoices=invoices,
        kpis=get_kpis(),
        chart=monthly_revenue(),
        breakdown=status_breakdown(),
        aging=aging_report(),
        statuses=STATUSES,
        status_filter=status,
        search=search,
        active_nav="dashboard",
    )


@dashboard_bp.route("/health")
def health():
    return jsonify({"status": "ok", "app": "Beejak"})
