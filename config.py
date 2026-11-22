"""Beejak — application configuration and brand constants.

Engineered by Raj Gautam • Jaunpur, Uttar Pradesh, India.
No phone or contact number is stored, displayed or generated anywhere.
"""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database" / "beejak.db"
ASSETS_DIR = BASE_DIR / "static" / "assets"


class Config:
    """Flask configuration object."""

    SECRET_KEY = os.environ.get("BEEJAK_SECRET_KEY", "beejak-local-dev-secret-key")
    DATABASE = str(DATABASE_PATH)
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    JSON_SORT_KEYS = False
    TEMPLATES_AUTO_RELOAD = True


# --------------------------------------------------------------------------- #
# Developer branding
# --------------------------------------------------------------------------- #
DEV_NAME = "Raj Gautam"
DEV_LOCATION = "Jaunpur, Uttar Pradesh, India"
DEV_EMAIL = "graj13099@gmail.com"
DEV_INSTAGRAM = "@linux.userraj"
DEV_GITHUB = "https://github.com/Rg100152"
DEV_TAGLINE = "Create crisp GST invoices, preview live, print PDF & track payments."
APP_TAGLINE = "Smart GST & Multi-Currency Invoice Generator"

CURRENCIES = {
    "INR": {"symbol": "₹", "label": "INR — Indian Rupee"},
    "USD": {"symbol": "$", "label": "USD — US Dollar"},
    "EUR": {"symbol": "€", "label": "EUR — Euro"},
}

TAX_RATES = [0, 5, 12, 18, 28]
TAX_MODES = {"CGST_SGST": "CGST + SGST", "IGST": "IGST"}
STATUSES = ["DRAFT", "SENT", "PAID", "OVERDUE"]

ACCENTS = {
    "emerald": {"label": "Emerald Corporate", "color": "#10B981"},
    "navy": {"label": "Midnight Navy", "color": "#1E3A8A"},
    "saffron": {"label": "Royal Saffron", "color": "#F59E0B"},
}

DEFAULT_UPI_ID = "rajgautam@upi"
DEFAULT_ACCENT = "emerald"
DEFAULT_TAX_RATE = 18
DEFAULT_TAX_MODE = "CGST_SGST"
PAYEE_NAME = "Raj Gautam"
UPI_APPS = ["GPay", "PhonePe", "Paytm", "BHIM"]
