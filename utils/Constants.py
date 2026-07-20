"""
Konstanta terpusat untuk CatatCuan AI.

Menaruh semua angka/limit di satu tempat memudahkan audit keamanan —
kalau suatu saat perlu menaikkan/menurunkan sebuah limit, cukup ubah
di sini, tidak perlu grep ke banyak file.
"""

import re
from pathlib import Path

import streamlit as st

# ── Batas Input & Anti-Abuse ─────────────────────────────────────────
MAX_INPUT_LENGTH = 1000          # panjang maksimum cerita transaksi
MAX_CHAT_LENGTH = 500            # panjang maksimum pertanyaan chat AI
MAX_AMOUNT = 10_000_000_000      # nominal transaksi maksimum (Rp 10 M)
MAX_TRANSACTIONS_PER_REQUEST = 50   # transaksi baru maksimum per sekali analisis
MAX_TOTAL_TRANSACTIONS = 5000       # total riwayat transaksi maksimum per sesi
RATE_LIMIT_SECONDS = 3              # jeda minimum antar permintaan ke Gemini

# ── Pola Validasi & Keamanan ─────────────────────────────────────────
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@", "\t", "\r")
SECRET_LIKE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9\-_]{10,}|AIza[A-Za-z0-9\-_]{20,})"
)

# ── Path Proyek ───────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
EXPORTS_DIR = ROOT_DIR / "exports"
PROMPTS_DIR = ROOT_DIR / "prompts"
FAVICON_PATH = ASSETS_DIR / "favicon.png"

# ── Mode Debug ────────────────────────────────────────────────────────
# HANYA aktif jika diset eksplisit lewat Streamlit Secrets. Jangan pernah
# menampilkan detail error mentah ke user biasa di production.
try:
    DEBUG_MODE = bool(st.secrets.get("DEBUG_MODE", False))
except (FileNotFoundError, KeyError):
    DEBUG_MODE = False
