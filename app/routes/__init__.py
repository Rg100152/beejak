"""Blueprint registry for Beejak."""
from __future__ import annotations

from app.routes.api_routes import api_bp
from app.routes.client_routes import clients_bp
from app.routes.dashboard_routes import dashboard_bp
from app.routes.invoice_routes import invoices_bp
from app.routes.payment_routes import payments_bp


def register_routes(app) -> None:
    for blueprint in (dashboard_bp, invoices_bp, clients_bp, payments_bp, api_bp):
        app.register_blueprint(blueprint)
