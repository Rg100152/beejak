"""Client directory and profile routes."""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models.client_model import client_invoices, create_client, get_client, list_clients
from app.utils.validators import is_valid_email

clients_bp = Blueprint("clients", __name__)


@clients_bp.route("/clients")
def directory():
    selected = None
    invoices = []
    client_id = request.args.get("id", type=int)
    if client_id:
        selected = get_client(client_id)
        invoices = client_invoices(client_id) if selected else []
    return render_template(
        "clients/directory.html",
        clients=list_clients(),
        selected=selected,
        client_invoices=invoices,
        active_nav="clients",
    )


@clients_bp.route("/clients", methods=["POST"])
def store():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    if not name:
        flash("Client name is required.", "error")
    elif email and not is_valid_email(email):
        flash("Please enter a valid email address.", "error")
    else:
        new_id = create_client(request.form.to_dict())
        flash(f"Client {name} added to the directory.", "success")
        return redirect(url_for("clients.directory", id=new_id))
    return redirect(url_for("clients.directory"))
