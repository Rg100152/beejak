"""Beejak Flask application factory."""
from __future__ import annotations

from datetime import date

from flask import Flask, render_template

from app.extensions import init_app
from app.routes import register_routes
from app.utils.formatters import amount_in_words, due_label, format_date, format_money
from config import (
    ACCENTS, APP_TAGLINE, CURRENCIES, DEFAULT_TAX_RATE, DEFAULT_UPI_ID,
    DEV_EMAIL, DEV_GITHUB, DEV_INSTAGRAM, DEV_LOCATION, DEV_NAME, DEV_TAGLINE,
    TAX_RATES, UPI_APPS, Config,
)


def create_app(config_object=Config) -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_object)

    init_app(app)
    register_routes(app)

    app.jinja_env.filters["money"] = format_money
    app.jinja_env.filters["words"] = amount_in_words
    app.jinja_env.filters["idate"] = format_date
    app.jinja_env.filters["due_label"] = due_label
    app.jinja_env.globals["due_label"] = due_label

    @app.context_processor
    def inject_brand():
        return {
            "dev_name": DEV_NAME,
            "dev_location": DEV_LOCATION,
            "dev_email": DEV_EMAIL,
            "dev_instagram": DEV_INSTAGRAM,
            "dev_github": DEV_GITHUB,
            "dev_tagline": DEV_TAGLINE,
            "app_tagline": APP_TAGLINE,
            "currencies": CURRENCIES,
            "tax_rates": TAX_RATES,
            "accents": ACCENTS,
            "upi_apps": UPI_APPS,
            "default_tax_rate": DEFAULT_TAX_RATE,
            "default_upi_id": DEFAULT_UPI_ID,
            "now_date": date.today().isoformat(),
        }

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("errors/500.html"), 500

    return app
