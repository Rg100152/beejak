"""Unit + smoke tests for Beejak billing logic.

    python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.services.payment_gateway import generate_utr, simulate_payment  # noqa: E402
from app.services.tax_calculator import calculate_totals  # noqa: E402
from app.services.upi_qr_service import build_upi_uri  # noqa: E402
from app.utils.formatters import amount_in_words, format_money, indian_group  # noqa: E402
from app.utils.validators import is_valid_email, is_valid_gstin, is_valid_upi_id  # noqa: E402
from config import Config  # noqa: E402


class TaxTests(unittest.TestCase):
    def test_cgst_sgst_split(self):
        result = calculate_totals(
            [{"description": "Service", "qty": 2, "unit_price": 50}],
            discount_pct=10, tax_pct=18,
        )
        self.assertEqual(result["subtotal"], 100.0)
        self.assertEqual(result["discount_amount"], 10.0)
        self.assertEqual(result["taxable_amount"], 90.0)
        self.assertEqual(result["tax_amount"], 16.2)
        self.assertEqual(result["cgst"], 8.1)
        self.assertEqual(result["sgst"], 8.1)
        self.assertEqual(result["grand_total"], 106.2)

    def test_igst_mode(self):
        result = calculate_totals(
            [{"qty": 1, "unit_price": 1000}], tax_pct=12, tax_mode="IGST"
        )
        self.assertEqual(result["igst"], 120.0)
        self.assertEqual(result["cgst"], 0.0)
        self.assertEqual(result["grand_total"], 1120.0)

    def test_empty_items(self):
        self.assertEqual(calculate_totals([])["grand_total"], 0.0)


class UpiTests(unittest.TestCase):
    def test_uri_format(self):
        uri = build_upi_uri("rajgautam@upi", 15000, "INR", "BJK-2026-104")
        self.assertTrue(uri.startswith("upi://pay?"))
        self.assertIn("pa=rajgautam%40upi", uri)
        self.assertIn("pn=Raj%20Gautam", uri)
        self.assertIn("am=15000.00", uri)
        self.assertIn("cu=INR", uri)
        self.assertIn("tn=BJK-2026-104", uri)


class FormatterTests(unittest.TestCase):
    def test_indian_grouping(self):
        self.assertEqual(indian_group(12345678), "1,23,45,678")
        self.assertEqual(format_money(123456.5), "₹1,23,456.50")
        self.assertEqual(format_money(4250, "USD"), "$4,250.00")

    def test_amount_in_words(self):
        self.assertEqual(amount_in_words(123456), "One Lakh Twenty Three Thousand Four Hundred Fifty Six Only")
        self.assertEqual(amount_in_words(0), "Zero Only")


class ValidatorTests(unittest.TestCase):
    def test_validators(self):
        self.assertTrue(is_valid_email("graj13099@gmail.com"))
        self.assertFalse(is_valid_email("not-an-email"))
        self.assertTrue(is_valid_upi_id("rajgautam@upi"))
        self.assertFalse(is_valid_upi_id("raj gautam"))
        self.assertTrue(is_valid_gstin("09AABCA1234K1ZP"))
        self.assertFalse(is_valid_gstin("BADGSTIN"))


class PaymentTests(unittest.TestCase):
    def test_utr_and_simulation(self):
        self.assertRegex(generate_utr(), r"^UTR\d{4}\d{9}$")
        result = simulate_payment("card", 1000)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["method"], "CARD")
        self.assertEqual(result["amount"], 1000)


class RouteSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(cls.tmpdir.name) / "test-beejak.db"

        class TestConfig(Config):
            DATABASE = str(db_path)
            TESTING = True

        cls.app = create_app(TestConfig)
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def test_pages_render(self):
        for path in ("/", "/invoices/create", "/clients", "/health"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)

    def test_calculate_api(self):
        response = self.client.post(
            "/api/calculate",
            json={"items": [{"qty": 2, "unit_price": 100}], "tax_pct": 18},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["grand_total"], 236.0)

    def test_create_and_pay_flow(self):
        response = self.client.post(
            "/api/invoices",
            json={
                "client_name": "Test Client", "client_email": "test@example.com",
                "items": [{"description": "Testing", "qty": 1, "unit_price": 1000}],
                "tax_pct": 0,
            },
        )
        self.assertEqual(response.status_code, 201)
        invoice_id = response.get_json()["id"]

        paid = self.client.post(f"/api/pay/{invoice_id}", json={"method": "UPI"})
        payload = paid.get_json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "PAID")
        self.assertRegex(payload["utr"], r"^UTR\d{13}$")

        receipt = self.client.get(payload["receipt_url"])
        self.assertEqual(receipt.status_code, 200)
        self.assertIn(payload["utr"], receipt.get_data(as_text=True))

    def test_csv_export(self):
        response = self.client.get("/api/export/csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("invoice_no,client_name", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
