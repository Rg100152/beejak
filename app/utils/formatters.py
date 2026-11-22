"""Indian money, date and number-to-word formatters."""
from __future__ import annotations

import calendar
from datetime import date, datetime

from config import CURRENCIES

_ONES = (
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
)
_TENS = (
    "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty",
    "Ninety",
)


def currency_symbol(currency: str = "INR") -> str:
    return CURRENCIES.get(currency, CURRENCIES["INR"])["symbol"]


def indian_group(number: int) -> str:
    """Group an integer using the Indian 1,23,45,678 system."""
    digits = str(number)
    if len(digits) <= 3:
        return digits
    head, tail = digits[:-3], digits[-3:]
    groups = []
    while head:
        groups.insert(0, head[-2:])
        head = head[:-2]
    return ",".join(groups + [tail])


def format_money(value, currency: str = "INR", decimals: bool = True) -> str:
    """Format an amount as e.g. ₹1,23,456.00 or $4,250.00."""
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0.0
    sign = "-" if number < 0 else ""
    number = abs(number)
    whole = int(number)
    fraction = int(round((number - whole) * 100))
    if fraction == 100:
        whole, fraction = whole + 1, 0
    body = indian_group(whole) if currency == "INR" else f"{whole:,}"
    if decimals:
        body += f".{fraction:02d}"
    return f"{sign}{currency_symbol(currency)}{body}"


def _two_digit_words(number: int) -> str:
    if number < 20:
        return _ONES[number]
    tens, ones = divmod(number, 10)
    return " ".join(filter(None, (_TENS[tens], _ONES[ones])))


def amount_in_words(value) -> str:
    """Convert an amount into Indian-system English words."""
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0.0
    rupees = int(number)
    paise = int(round((number - rupees) * 100))
    if paise == 100:
        rupees, paise = rupees + 1, 0
    if rupees == 0 and paise == 0:
        return "Zero Only"

    parts = []
    crores, remainder = divmod(rupees, 10_000_000)
    lakhs, remainder = divmod(remainder, 100_000)
    thousands, hundreds = divmod(remainder, 1000)

    if crores:
        parts.append(f"{_two_digit_words(crores)} Crore")
    if lakhs:
        parts.append(f"{_two_digit_words(lakhs)} Lakh")
    if thousands:
        parts.append(f"{_two_digit_words(thousands)} Thousand")
    hundred_digit, rest = divmod(hundreds, 100)
    if hundred_digit:
        parts.append(f"{_ONES[hundred_digit]} Hundred")
    if rest:
        parts.append(_two_digit_words(rest))

    text = " ".join(parts).strip() or "Zero"
    if paise:
        text += f" and {_two_digit_words(paise)} Paise"
    return text + " Only"


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d %b %Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def format_date(value: str | None, fmt: str = "%d %b %Y") -> str:
    parsed = parse_date(value)
    return parsed.strftime(fmt) if parsed else "—"


def month_name(year: int, month: int) -> str:
    """Return a short month label such as 'Apr 26'."""
    return f"{calendar.month_abbr[month]} {year % 100:02d}"


def due_label(due_date: str, status: str = "DRAFT") -> str:
    due = parse_date(due_date)
    if due is None:
        return "—"
    if status == "PAID":
        return "Settled"
    days = (due - date.today()).days
    if days < 0:
        return f"Overdue by {abs(days)}d"
    if days == 0:
        return "Due today"
    return f"In {days}d"
