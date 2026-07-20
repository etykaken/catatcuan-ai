"""
Normalisasi dan sanitasi nilai mentah yang berasal dari respons AI
atau input pengguna, sebelum data tersebut dipakai di bagian lain
aplikasi (session state, Excel, dsb).
"""

from datetime import date, timedelta

from utils.constants import FORMULA_TRIGGER_CHARS, ISO_DATE_PATTERN, SECRET_LIKE_PATTERN


def resolve_date(value: str) -> str:
    """Mengubah tanggal relatif dari AI menjadi tanggal aktual.

    Nilai yang tidak dikenali atau tidak valid akan fallback dengan
    aman ke hari ini, alih-alih diloloskan mentah-mentah ke data.
    """
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
    """Konversi nilai amount ke int secara aman.

    - Menolak bool secara eksplisit (bool adalah subclass int di Python).
    - Menerima float HANYA jika nilainya bulat (tanpa pembulatan diam-diam).
    - Menerima string angka sebagai jaring pengaman.
    - Selain itu, dianggap tidak valid (return None).
    """
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


def sanitize_text_field(value, max_length: int) -> str:
    """Bersihkan teks bebas dari karakter kontrol dan batasi panjangnya."""
    text = "".join(
        ch for ch in str(value).strip() if ch.isprintable() or ch == "\n"
    )
    return text[:max_length]


def sanitize_excel_cell(text: str) -> str:
    """Cegah Formula Injection saat file dibuka di Excel/Google Sheets."""
    text = str(text)
    return "'" + text if text.startswith(FORMULA_TRIGGER_CHARS) else text


def redact_secret_like_strings(text: str, api_key: str | None = None) -> str:
    """Sensor string yang mirip API key sebelum ditampilkan ke user."""
    if api_key:
        text = text.replace(api_key, "[REDACTED]")
    return SECRET_LIKE_PATTERN.sub("[REDACTED]", text)
