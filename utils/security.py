import re

FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@", "\t", "\r")
SECRET_LIKE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9\-_]{10,}|AIza[A-Za-z0-9\-_]{20,}|gsk_[A-Za-z0-9]{10,})"
)


def sanitize_text(value, max_length: int) -> str:
    text = "".join(
        char for char in str(value).strip()
        if char.isprintable() or char == "\n"
    )
    return text[:max_length]


def sanitize_excel_cell(value: str) -> str:
    text = str(value)
    return "'" + text if text.startswith(FORMULA_TRIGGER_CHARS) else text


def redact_secret_like_strings(text: str, api_key: str | None = None) -> str:
    if api_key:
        text = text.replace(api_key, "[REDACTED]")
    return SECRET_LIKE_PATTERN.sub("[REDACTED]", text)
