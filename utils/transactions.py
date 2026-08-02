import re
from datetime import date, timedelta

from config import (
    MAX_AMOUNT,
    MAX_TRANSACTIONS_PER_REQUEST,
)
from utils.security import sanitize_excel_cell, sanitize_text

ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def resolve_date(value: str) -> str:
    today = date.today()
    normalized = str(value).strip().upper()

    if normalized == "TODAY":
        return today.isoformat()
    if normalized == "YESTERDAY":
        return (today - timedelta(days=1)).isoformat()
    if normalized == "TOMORROW":
        return (today + timedelta(days=1)).isoformat()

    candidate = str(value).strip()
    if ISO_DATE_PATTERN.match(candidate):
        try:
            date.fromisoformat(candidate)
            return candidate
        except ValueError:
            pass

    return today.isoformat()


def coerce_amount(raw_amount) -> int | None:
    if isinstance(raw_amount, bool):
        return None
    if isinstance(raw_amount, int):
        return raw_amount
    if isinstance(raw_amount, float):
        return int(raw_amount) if raw_amount.is_integer() else None
    if isinstance(raw_amount, str):
        cleaned = raw_amount.strip().replace(".", "").replace(",", "")
        return int(cleaned) if cleaned.isdigit() else None
    return None


def validate_transactions(raw_transactions: list) -> list:
    validated = []

    if not isinstance(raw_transactions, list):
        return validated

    for item in raw_transactions[:MAX_TRANSACTIONS_PER_REQUEST]:
        if not isinstance(item, dict):
            continue

        transaction_type = str(item.get("type", "")).lower()
        if transaction_type not in {"income", "expense"}:
            continue

        amount = coerce_amount(item.get("amount"))
        if amount is None or amount <= 0 or amount > MAX_AMOUNT:
            continue

        validated.append(
            {
                "Tanggal": resolve_date(item.get("date", "TODAY")),
                "Deskripsi": sanitize_excel_cell(
                    sanitize_text(item.get("description", ""), 120)
                ),
                "Kategori": sanitize_excel_cell(
                    sanitize_text(item.get("category", "Lainnya"), 60)
                ),
                "Tipe": (
                    "Pemasukan"
                    if transaction_type == "income"
                    else "Pengeluaran"
                ),
                "Jumlah": amount,
                "Perlu Konfirmasi": (
                    "Ya"
                    if item.get("requires_confirmation", False)
                    else "Tidak"
                ),
            }
        )

    return validated
