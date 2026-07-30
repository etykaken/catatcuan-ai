
import html
import re
import time
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from services.gemini_service import (
    analyze_transactions,
    ask_financial_assistant,
)

# =========================================================
# KONFIGURASI
# =========================================================
MAX_INPUT_LENGTH = 500
MAX_CHAT_LENGTH = 500
MAX_AMOUNT = 10_000_000_000
MAX_TRANSACTIONS_PER_REQUEST = 50
MAX_TOTAL_TRANSACTIONS = 5000
RATE_LIMIT_SECONDS = 3

ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@", "\t", "\r")
SECRET_LIKE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9\-_]{10,}|AIza[A-Za-z0-9\-_]{20,})"
)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
FAVICON_PATH = ASSETS_DIR / "favicon.png"

try:
    DEBUG_MODE = bool(st.secrets.get("DEBUG_MODE", False))
except (FileNotFoundError, KeyError):
    DEBUG_MODE = False


# =========================================================
# HELPER
# =========================================================
def format_rupiah(value: int | float) -> str:
    return f"Rp{value:,.0f}".replace(",", ".")


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


def sanitize_text(value, max_length: int) -> str:
    text = "".join(
        character
        for character in str(value).strip()
        if character.isprintable() or character == "\n"
    )
    return text[:max_length]


def sanitize_excel_cell(value: str) -> str:
    text = str(value)
    return "'" + text if text.startswith(FORMULA_TRIGGER_CHARS) else text


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


def redact_secret_like_strings(
    text: str,
    api_key: str | None = None,
) -> str:
    if api_key:
        text = text.replace(api_key, "[REDACTED]")
    return SECRET_LIKE_PATTERN.sub("[REDACTED]", text)


def create_excel_report(
    dataframe: pd.DataFrame,
    total_income: int,
    total_expense: int,
    net_result: int,
    expense_ratio: float,
) -> BytesIO:
    buffer = BytesIO()

    summary = pd.DataFrame(
        {
            "Keterangan": [
                "Total Pemasukan",
                "Total Pengeluaran",
                "Laba/Rugi Bersih",
                "Rasio Pengeluaran",
                "Jumlah Transaksi",
                "Tanggal Laporan",
            ],
            "Nilai": [
                total_income,
                total_expense,
                net_result,
                f"{expense_ratio:.1f}%",
                len(dataframe),
                datetime.now().strftime("%d-%m-%Y %H:%M"),
            ],
        }
    )

    export_dataframe = dataframe.copy()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        export_dataframe.to_excel(
            writer,
            index=False,
            sheet_name="Transaksi",
        )
        summary.to_excel(
            writer,
            index=False,
            sheet_name="Ringkasan",
        )

        transaction_sheet = writer.book["Transaksi"]
        summary_sheet = writer.book["Ringkasan"]

        transaction_widths = {
            "A": 17,
            "B": 34,
            "C": 22,
            "D": 18,
            "E": 18,
            "F": 20,
        }
        for column, width in transaction_widths.items():
            transaction_sheet.column_dimensions[column].width = width

        summary_sheet.column_dimensions["A"].width = 25
        summary_sheet.column_dimensions["B"].width = 24

        for cell in transaction_sheet[1]:
            cell.font = cell.font.copy(bold=True)

        for cell in summary_sheet[1]:
            cell.font = cell.font.copy(bold=True)

        for row in range(2, transaction_sheet.max_row + 1):
            transaction_sheet[f"E{row}"].number_format = '"Rp"#,##0'

        for cell_address in ("B2", "B3", "B4"):
            summary_sheet[cell_address].number_format = '"Rp"#,##0'

        transaction_sheet.freeze_panes = "A2"
        summary_sheet.freeze_panes = "A2"

    buffer.seek(0)
    return buffer


def render_metric_card(
    title: str,
    value: str,
    icon: str,
    theme: str,
) -> None:
    st.markdown(
        f"""
        <div class="metric-card metric-{theme}">
            <div class="metric-title">{html.escape(title)}</div>
            <div class="metric-value">{html.escape(value)}</div>
            <div class="metric-icon">{icon}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_insights(
    dataframe: pd.DataFrame,
    total_income: int,
    total_expense: int,
    net_result: int,
    expense_ratio: float,
) -> list[str]:
    if dataframe.empty:
        return [
            "Belum ada transaksi. Masukkan transaksi pertama untuk melihat analisis.",
            "Catat transaksi menggunakan bahasa sehari-hari.",
            "CatatCuan AI akan menyusun transaksi menjadi data terstruktur.",
        ]

    insights = []

    if net_result > 0:
        insights.append(
            f"Usaha kamu hari ini memperoleh laba bersih sebesar "
            f"<strong>{format_rupiah(net_result)}</strong>."
        )
    elif net_result < 0:
        insights.append(
            f"Usaha kamu hari ini mengalami kerugian sebesar "
            f"<strong>{format_rupiah(abs(net_result))}</strong>."
        )
    else:
        insights.append(
            "Pemasukan dan pengeluaran saat ini berada pada posisi impas."
        )

    expenses = dataframe[dataframe["Tipe"] == "Pengeluaran"]

    if not expenses.empty:
        category_totals = (
            expenses.groupby("Kategori")["Jumlah"]
            .sum()
            .sort_values(ascending=False)
        )
        largest_category = str(category_totals.index[0])
        largest_amount = int(category_totals.iloc[0])
        share = (
            largest_amount / total_expense * 100
            if total_expense > 0
            else 0
        )

        insights.append(
            f"Pengeluaran terbesar berasal dari kategori "
            f"<strong>{html.escape(largest_category)}</strong> "
            f"({share:.0f}% dari total pengeluaran)."
        )
    else:
        insights.append("Belum ada pengeluaran yang tercatat.")

    if total_income > 0:
        if expense_ratio <= 50:
            condition = "Masih dalam kondisi yang sehat."
        elif expense_ratio <= 80:
            condition = "Perlu mulai diawasi."
        else:
            condition = "Cukup tinggi dan perlu segera dievaluasi."

        insights.append(
            f"Rasio pengeluaran terhadap pemasukan adalah "
            f"<strong>{expense_ratio:.0f}%</strong>. {condition}"
        )
    else:
        insights.append(
            "Belum ada pemasukan untuk menghitung rasio pengeluaran."
        )

    return insights


def render_chat_bubble(role: str, message: str) -> None:
    safe_message = html.escape(str(message)).replace("\n", "<br>")
    current_time = datetime.now().strftime("%H:%M")

    if role == "user":
        st.markdown(
            f"""
            <div class="chat-row chat-user-row">
                <div class="chat-bubble chat-user">
                    {safe_message}
                    <span class="chat-time">{current_time} ✓✓</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="chat-row chat-ai-row">
                <div class="chat-avatar">🤖</div>
                <div class="chat-bubble chat-ai">
                    {safe_message}
                    <span class="chat-time">{current_time}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# PAGE
# =========================================================
st.set_page_config(
    page_title="CatatCuan AI",
    page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else "🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --green: #119447;
        --green-dark: #087a36;
        --green-pale: #edf9f1;
        --orange: #ff5b15;
        --orange-pale: #fff3eb;
        --ink: #151c2b;
        --muted: #657269;
        --line: #e4ebe6;
        --card: #ffffff;
        --page: #fbfdfb;
    }

    * {
        box-sizing: border-box;
    }

    html {
        scroll-behavior: smooth;
    }

    body,
    .stApp,
    [class*="css"] {
        font-family: Inter, ui-sans-serif, system-ui, -apple-system,
        BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .stApp {
        background: var(--page);
    }

    .block-container {
        max-width: 1240px;
        padding-top: 1rem;
        padding-bottom: 2.5rem;
    }

    [data-testid="stSidebar"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    #MainMenu,
    footer,
    header {
        visibility: hidden;
    }

    [data-testid="stToolbar"] {
        display: none;
    }

    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-height: 66px;
        margin-bottom: 18px;
    }

    .brand-wrap {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .brand-logo {
        width: 45px;
        height: 45px;
        display: grid;
        place-items: center;
        border-radius: 14px;
        background: #e8f7ed;
        font-size: 27px;
    }

    .brand-name {
        color: var(--ink);
        font-size: 21px;
        font-weight: 850;
        letter-spacing: -.03em;
    }

    .brand-subtitle {
        color: var(--muted);
        font-size: 12px;
        margin-top: 2px;
    }

    .profile-pill {
        display: flex;
        align-items: center;
        gap: 9px;
        padding: 7px 12px 7px 7px;
        border: 1px solid var(--line);
        border-radius: 999px;
        background: white;
        box-shadow: 0 5px 18px rgba(16, 60, 35, .05);
    }

    .profile-avatar {
        width: 34px;
        height: 34px;
        display: grid;
        place-items: center;
        border-radius: 50%;
        background: #ecf7ef;
    }

    .profile-name {
        color: var(--ink);
        font-size: 13px;
        font-weight: 750;
    }

    .hero {
        position: relative;
        min-height: 290px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        overflow: hidden;
        margin-bottom: 18px;
        padding: 35px 38px;
        border: 1px solid #daeadf;
        border-radius: 16px;
        background:
            radial-gradient(circle at 72% 22%, rgba(61, 193, 104, .18), transparent 22%),
            linear-gradient(135deg, #fbfffc, #eaf8ef);
    }

    .hero-copy {
        position: relative;
        z-index: 3;
        max-width: 580px;
    }

    .hero-title {
        color: var(--ink);
        font-size: 37px;
        line-height: 1.15;
        font-weight: 900;
        letter-spacing: -.045em;
    }

    .hero-title span {
        color: var(--green);
    }

    .hero-description {
        max-width: 560px;
        margin-top: 17px;
        color: #29332d;
        font-size: 15px;
        line-height: 1.55;
    }

    .hero-visual {
        position: relative;
        width: 390px;
        height: 210px;
        flex: 0 0 390px;
    }

    .robot-body {
        position: absolute;
        right: 100px;
        bottom: -5px;
        width: 125px;
        height: 150px;
        border-radius: 55px 55px 20px 20px;
        background: linear-gradient(145deg, #72d18c, #329f58);
    }

    .robot-head {
        position: absolute;
        right: 90px;
        top: 18px;
        z-index: 3;
        width: 145px;
        height: 94px;
        display: grid;
        place-items: center;
        border: 12px solid #5bc37c;
        border-radius: 42px;
        color: white;
        background: #182237;
        font-size: 42px;
    }

    .robot-antenna {
        position: absolute;
        right: 157px;
        top: -1px;
        width: 5px;
        height: 24px;
        background: #2d9d56;
    }

    .robot-antenna::before {
        content: "";
        position: absolute;
        left: -5px;
        top: -7px;
        width: 15px;
        height: 15px;
        border-radius: 50%;
        background: #75cf41;
    }

    .robot-laptop {
        position: absolute;
        right: 41px;
        bottom: 0;
        z-index: 4;
        width: 145px;
        height: 80px;
        border-radius: 8px 8px 15px 15px;
        transform: skew(-6deg);
        background: linear-gradient(135deg, #858d9f, #666f82);
    }

    .hero-floating {
        position: absolute;
        z-index: 5;
        min-width: 120px;
        padding: 12px 14px;
        border: 1px solid #e1eae3;
        border-radius: 13px;
        background: rgba(255,255,255,.94);
        box-shadow: 0 8px 22px rgba(26, 76, 46, .09);
        font-size: 11px;
    }

    .hero-floating strong {
        display: block;
        margin-top: 3px;
        font-size: 14px;
    }

    .hero-income {
        top: 4px;
        right: 202px;
        color: var(--green);
    }

    .hero-expense {
        top: 70px;
        right: 0;
        color: var(--orange);
    }

    .hero-chart-icon {
        position: absolute;
        right: 3px;
        top: 2px;
        width: 50px;
        height: 50px;
        display: grid;
        place-items: center;
        border-radius: 14px;
        color: var(--green);
        background: white;
        box-shadow: 0 8px 20px rgba(26, 76, 46, .09);
        font-size: 26px;
    }

    .section-title {
        display: flex;
        align-items: center;
        gap: 9px;
        margin: 0 0 7px;
        color: var(--ink);
        font-size: 17px;
        font-weight: 850;
    }

    .section-number {
        width: 23px;
        height: 23px;
        display: inline-grid;
        place-items: center;
        border-radius: 5px;
        color: white;
        background: var(--green);
        font-size: 12px;
        font-weight: 850;
    }

    .section-helper {
        margin-bottom: 11px;
        color: var(--muted);
        font-size: 12px;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: white;
        box-shadow: 0 6px 20px rgba(23, 66, 40, .06);
    }

    [data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 15px;
    }

    .stTextArea textarea,
    .stTextInput input {
        border: 1px solid #d8e2da;
        border-radius: 9px;
        background: #fff;
        color: var(--ink);
        font-size: 14px;
    }

    .stTextArea textarea:focus,
    .stTextInput input:focus {
        border-color: var(--green);
        box-shadow: 0 0 0 3px rgba(17, 148, 71, .10);
    }

    .stButton button[kind="primary"],
    .stDownloadButton button {
        min-height: 42px;
        border: 0;
        border-radius: 7px;
        color: white;
        background: linear-gradient(90deg, #07913f, #0aa24b);
        font-weight: 750;
    }

    .stButton button[kind="primary"]:hover,
    .stDownloadButton button:hover {
        color: white;
        border: 0;
        background: var(--green-dark);
    }

    .stButton button:not([kind="primary"]) {
        border: 1px solid #dce5de;
        border-radius: 7px;
        color: var(--green-dark);
        background: white;
    }

    .metric-card {
        min-height: 157px;
        padding: 23px 15px;
        border: 1px solid #dcebe0;
        border-radius: 10px;
        text-align: center;
    }

    .metric-green {
        background: linear-gradient(145deg, #f7fcf8, #edf9f1);
    }

    .metric-orange {
        border-color: #f6dccd;
        background: linear-gradient(145deg, #fffaf7, #fff1e8);
    }

    .metric-title {
        color: var(--green-dark);
        font-size: 12px;
    }

    .metric-orange .metric-title {
        color: var(--orange);
    }

    .metric-value {
        margin: 19px 0 14px;
        color: #087432;
        font-size: 22px;
        font-weight: 850;
    }

    .metric-orange .metric-value {
        color: #e94a0a;
    }

    .metric-icon {
        width: 37px;
        height: 37px;
        display: grid;
        place-items: center;
        margin: auto;
        border: 2px solid currentColor;
        border-radius: 50%;
        color: var(--green);
        font-size: 21px;
    }

    .metric-orange .metric-icon {
        color: var(--orange);
    }

    .update-strip {
        margin-top: 12px;
        padding: 9px 12px;
        border-radius: 7px;
        color: #718078;
        background: #f2f8f4;
        font-size: 11px;
    }

    .insight-list {
        display: grid;
        gap: 8px;
    }

    .insight-item {
        display: flex;
        gap: 11px;
        align-items: center;
        min-height: 56px;
        padding: 11px;
        border: 1px solid #e1e7e3;
        border-radius: 8px;
        color: #1d2821;
        background: #fff;
        font-size: 12px;
        line-height: 1.45;
    }

    .insight-check {
        width: 23px;
        height: 23px;
        flex: 0 0 23px;
        display: grid;
        place-items: center;
        border-radius: 50%;
        color: white;
        background: var(--green);
        font-size: 12px;
        font-weight: 800;
    }

    .gemini-label {
        margin-top: 11px;
        color: var(--green);
        font-size: 11px;
        font-weight: 700;
    }

    .chat-row {
        display: flex;
        margin: 8px 0;
    }

    .chat-user-row {
        justify-content: flex-end;
    }

    .chat-ai-row {
        align-items: flex-start;
        gap: 8px;
    }

    .chat-avatar {
        width: 30px;
        height: 30px;
        display: grid;
        place-items: center;
        flex: 0 0 30px;
        border-radius: 50%;
        background: #e8f7ed;
    }

    .chat-bubble {
        max-width: 90%;
        padding: 10px 12px 7px;
        border-radius: 8px;
        color: #273029;
        font-size: 12px;
        line-height: 1.45;
    }

    .chat-user {
        border: 1px solid #d8eadc;
        background: #eaf8ee;
    }

    .chat-ai {
        border: 1px solid #e2e7e3;
        background: #fafbfa;
    }

    .chat-time {
        display: block;
        margin-top: 4px;
        color: #7b8780;
        font-size: 9px;
        text-align: right;
    }

    .empty-box {
        padding: 26px 15px;
        border: 1px dashed #d3ded6;
        border-radius: 9px;
        color: var(--muted);
        background: #fbfdfb;
        text-align: center;
        font-size: 12px;
    }

    [data-testid="stDataFrame"] {
        border: 0;
    }

    .export-copy {
        min-height: 46px;
        display: flex;
        align-items: center;
        color: var(--muted);
        font-size: 12px;
    }

    .footer-copy {
        padding: 24px 0 4px;
        color: #69756d;
        font-size: 12px;
        text-align: center;
    }

    @media (max-width: 900px) {
        .block-container {
            padding-left: 12px;
            padding-right: 12px;
        }

        .profile-pill {
            display: none;
        }

        .hero {
            min-height: 250px;
            padding: 28px 22px;
        }

        .hero-title {
            font-size: 30px;
        }

        .hero-visual {
            display: none;
        }

        .metric-card {
            min-height: 135px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================
if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0.0

if "last_chat_request_time" not in st.session_state:
    st.session_state.last_chat_request_time = 0.0


# =========================================================
# HEADER + HERO
# =========================================================
st.markdown(
    """
    <div class="topbar">
        <div class="brand-wrap">
            <div class="brand-logo">🤖</div>
            <div>
                <div class="brand-name">CatatCuan AI</div>
                <div class="brand-subtitle">AI Financial Assistant</div>
            </div>
        </div>
        <div class="profile-pill">
            <div class="profile-avatar">👩🏻</div>
            <div class="profile-name">Etyka K.</div>
            <div>⌄</div>
        </div>
    </div>

    <section class="hero">
        <div class="hero-copy">
            <div class="hero-title">
                Catat pemasukan &amp; pengeluaran<br>
                semudah <span>bercerita.</span>
            </div>
            <div class="hero-description">
                AI membantu membaca transaksi, membuat pencatatan otomatis,
                serta memberikan insight keuangan usaha.
            </div>
        </div>

        <div class="hero-visual" aria-hidden="true">
            <div class="hero-floating hero-income">
                Pemasukan
                <strong>Rp300.000</strong>
            </div>
            <div class="hero-floating hero-expense">
                Pengeluaran
                <strong>Rp85.000</strong>
            </div>
            <div class="hero-chart-icon">📈</div>
            <div class="robot-antenna"></div>
            <div class="robot-body"></div>
            <div class="robot-head">⌣</div>
            <div class="robot-laptop"></div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# DATA SUMMARY
# =========================================================
if st.session_state.transactions:
    dataframe = pd.DataFrame(st.session_state.transactions)
else:
    dataframe = pd.DataFrame(
        columns=[
            "Tanggal",
            "Deskripsi",
            "Kategori",
            "Tipe",
            "Jumlah",
            "Perlu Konfirmasi",
        ]
    )

total_income = int(
    dataframe.loc[dataframe["Tipe"] == "Pemasukan", "Jumlah"].sum()
) if not dataframe.empty else 0

total_expense = int(
    dataframe.loc[dataframe["Tipe"] == "Pengeluaran", "Jumlah"].sum()
) if not dataframe.empty else 0

net_result = total_income - total_expense
expense_ratio = (
    total_expense / total_income * 100
    if total_income > 0
    else 0.0
)


# =========================================================
# INPUT + SUMMARY
# =========================================================
left_column, right_column = st.columns([1, 1], gap="medium")

with left_column:
    with st.container(border=True):
        st.markdown(
            """
            <div class="section-title">
                <span class="section-number">1</span>
                ✍️ Catat Transaksi
            </div>
            <div class="section-helper">
                Tulis transaksi harianmu dengan bahasa alami.
            </div>
            <div class="section-helper">
                💡 Contoh: jual kopi 300 ribu, beli susu 80 ribu,
                bayar parkir 5 ribu
            </div>
            """,
            unsafe_allow_html=True,
        )

        transaction_text = st.text_area(
            "Transaksi",
            placeholder=(
                "Hari ini jual kopi 300 ribu\n"
                "beli susu 80 ribu\n"
                "bayar parkir 5 ribu"
            ),
            height=128,
            max_chars=MAX_INPUT_LENGTH,
            label_visibility="collapsed",
        )

        st.caption(
            f"{len(transaction_text)} / {MAX_INPUT_LENGTH} karakter"
        )

        analyze_button = st.button(
            "✨ Analisis & Tambahkan Transaksi",
            type="primary",
            use_container_width=True,
        )

with right_column:
    with st.container(border=True):
        st.markdown(
            """
            <div class="section-title">
                <span class="section-number">◉</span>
                Ringkasan Hari Ini
            </div>
            """,
            unsafe_allow_html=True,
        )

        metric_columns = st.columns(3, gap="small")

        with metric_columns[0]:
            render_metric_card(
                "Total Pemasukan",
                format_rupiah(total_income),
                "↑",
                "green",
            )

        with metric_columns[1]:
            render_metric_card(
                "Total Pengeluaran",
                format_rupiah(total_expense),
                "↓",
                "orange",
            )

        with metric_columns[2]:
            render_metric_card(
                "Laba Bersih" if net_result >= 0 else "Kerugian",
                format_rupiah(abs(net_result)),
                "⌁",
                "green" if net_result >= 0 else "orange",
            )

        st.markdown(
            f"""
            <div class="update-strip">
                ◉ Update terakhir:
                {datetime.now().strftime("%d %b %Y, %H:%M")}
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# ANALYZE ACTION
# =========================================================
if analyze_button:
    now = time.time()

    if now - st.session_state.last_request_time < RATE_LIMIT_SECONDS:
        st.warning("Tunggu beberapa detik sebelum mengirim lagi.")

    elif not transaction_text.strip():
        st.warning("Tulis transaksi terlebih dahulu.")

    else:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except (FileNotFoundError, KeyError):
            st.error("GEMINI_API_KEY belum dipasang di Streamlit Secrets.")
        else:
            try:
                st.session_state.last_request_time = now

                with st.spinner(
                    "CatatCuan AI sedang membaca transaksi..."
                ):
                    result = analyze_transactions(
                        api_key=api_key,
                        user_input=transaction_text.strip()[
                            :MAX_INPUT_LENGTH
                        ],
                    )

                raw_transactions = (
                    result.get("transactions", [])
                    if isinstance(result, dict)
                    else []
                )
                new_transactions = validate_transactions(
                    raw_transactions
                )

                if not new_transactions:
                    st.warning(
                        "Tidak ditemukan transaksi yang bisa dicatat."
                    )
                else:
                    remaining_slots = (
                        MAX_TOTAL_TRANSACTIONS
                        - len(st.session_state.transactions)
                    )

                    if remaining_slots <= 0:
                        st.warning(
                            "Riwayat transaksi sudah mencapai batas."
                        )
                    else:
                        st.session_state.transactions.extend(
                            new_transactions[:remaining_slots]
                        )
                        st.success(
                            f"{min(len(new_transactions), remaining_slots)} "
                            "transaksi berhasil ditambahkan."
                        )
                        st.rerun()

            except Exception as error:
                st.error(
                    "Transaksi gagal diproses. Silakan coba lagi."
                )

                if DEBUG_MODE:
                    with st.expander("Detail error"):
                        st.code(
                            redact_secret_like_strings(
                                str(error),
                                api_key,
                            )
                        )


# =========================================================
# INSIGHT + CHART
# =========================================================
insight_column, chart_column = st.columns(
    [1, 1],
    gap="medium",
)

with insight_column:
    with st.container(border=True):
        st.markdown(
            """
            <div class="section-title">
                <span class="section-number">2</span>
                🤖 AI Financial Insight
            </div>
            <div class="section-helper">
                Berikut analisis keuangan usahamu hari ini.
            </div>
            """,
            unsafe_allow_html=True,
        )

        insight_items = build_insights(
            dataframe,
            total_income,
            total_expense,
            net_result,
            expense_ratio,
        )

        insight_html = '<div class="insight-list">'
        for item in insight_items:
            insight_html += (
                '<div class="insight-item">'
                '<div class="insight-check">✓</div>'
                f'<div>{item}</div>'
                '</div>'
            )
        insight_html += "</div>"

        st.markdown(insight_html, unsafe_allow_html=True)
        st.markdown(
            '<div class="gemini-label">'
            '✣ Insight dihasilkan oleh Gemini AI'
            '</div>',
            unsafe_allow_html=True,
        )

with chart_column:
    with st.container(border=True):
        chart_header_left, chart_header_right = st.columns(
            [2.4, 1]
        )

        with chart_header_left:
            st.markdown(
                """
                <div class="section-title">
                    📊 Grafik Arus Kas
                </div>
                """,
                unsafe_allow_html=True,
            )

        with chart_header_right:
            st.selectbox(
                "Periode",
                ["Hari Ini"],
                label_visibility="collapsed",
            )

        chart_data = pd.DataFrame(
            {
                "Jenis": ["Pemasukan", "Pengeluaran"],
                "Nominal": [total_income, total_expense],
            }
        ).set_index("Jenis")

        st.bar_chart(
            chart_data,
            height=245,
            use_container_width=True,
        )


# =========================================================
# CHAT
# =========================================================
with st.container(border=True):
    chat_header_left, chat_header_right = st.columns(
        [4, 1]
    )

    with chat_header_left:
        st.markdown(
            """
            <div class="section-title">
                <span class="section-number">3</span>
                💬 Tanya CatatCuan AI
            </div>
            <div class="section-helper">
                Tanyakan apa saja tentang keuangan usahamu.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with chat_header_right:
        clear_chat_button = st.button(
            "🗑 Bersihkan Chat",
            use_container_width=True,
        )

    chat_input_column, chat_result_column = st.columns(
        [1, 1],
        gap="medium",
    )

    with chat_input_column:
        chat_question = st.text_area(
            "Pertanyaan",
            placeholder="Contoh: Apakah pengeluaran saya sehat?",
            height=105,
            max_chars=MAX_CHAT_LENGTH,
            label_visibility="collapsed",
        )

        ask_button = st.button(
            "➤ Tanya AI",
            type="primary",
            use_container_width=True,
        )

    with chat_result_column:
        if st.session_state.chat_history:
            for chat_item in st.session_state.chat_history[-6:]:
                render_chat_bubble(
                    chat_item["role"],
                    chat_item["message"],
                )
        else:
            st.markdown(
                """
                <div class="empty-box">
                    Belum ada percakapan.<br>
                    Tanyakan kondisi keuangan berdasarkan transaksimu.
                </div>
                """,
                unsafe_allow_html=True,
            )

if clear_chat_button:
    st.session_state.chat_history = []
    st.rerun()

if ask_button:
    now = time.time()

    if dataframe.empty:
        st.warning(
            "Tambahkan transaksi sebelum bertanya kepada AI."
        )

    elif not chat_question.strip():
        st.warning("Tulis pertanyaan terlebih dahulu.")

    elif (
        now - st.session_state.last_chat_request_time
        < RATE_LIMIT_SECONDS
    ):
        st.warning("Tunggu beberapa detik sebelum bertanya lagi.")

    else:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except (FileNotFoundError, KeyError):
            st.error("GEMINI_API_KEY belum dipasang di Streamlit Secrets.")
        else:
            safe_question = chat_question.strip()[:MAX_CHAT_LENGTH]

            try:
                st.session_state.last_chat_request_time = now

                with st.spinner(
                    "CatatCuan AI sedang menganalisis..."
                ):
                    answer = ask_financial_assistant(
                        api_key=api_key,
                        question=safe_question,
                        transactions=st.session_state.transactions,
                    )

                st.session_state.chat_history.extend(
                    [
                        {
                            "role": "user",
                            "message": safe_question,
                        },
                        {
                            "role": "assistant",
                            "message": str(answer),
                        },
                    ]
                )
                st.rerun()

            except Exception as error:
                st.error(
                    "CatatCuan AI gagal menjawab. Coba lagi."
                )

                if DEBUG_MODE:
                    with st.expander("Detail error"):
                        st.code(
                            redact_secret_like_strings(
                                str(error),
                                api_key,
                            )
                        )


# =========================================================
# HISTORY
# =========================================================
with st.container(border=True):
    history_header_left, history_header_right = st.columns(
        [4, 1]
    )

    with history_header_left:
        st.markdown(
            """
            <div class="section-title">
                <span class="section-number">4</span>
                🧾 Riwayat Transaksi
            </div>
            """,
            unsafe_allow_html=True,
        )

    with history_header_right:
        transaction_filter = st.selectbox(
            "Filter",
            ["Semua", "Pemasukan", "Pengeluaran"],
            label_visibility="collapsed",
        )

    if dataframe.empty:
        st.markdown(
            """
            <div class="empty-box">
                Belum ada transaksi.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        filtered_dataframe = dataframe.copy()

        if transaction_filter != "Semua":
            filtered_dataframe = filtered_dataframe[
                filtered_dataframe["Tipe"] == transaction_filter
            ]

        table_dataframe = filtered_dataframe[
            ["Tanggal", "Deskripsi", "Kategori", "Tipe", "Jumlah"]
        ].copy()

        table_dataframe["Tanggal"] = pd.to_datetime(
            table_dataframe["Tanggal"],
            errors="coerce",
        ).dt.strftime("%d %b %Y, %H:%M").fillna(
            table_dataframe["Tanggal"]
        )

        st.dataframe(
            table_dataframe,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Tanggal": st.column_config.TextColumn(
                    "Tanggal",
                    width="medium",
                ),
                "Deskripsi": st.column_config.TextColumn(
                    "Deskripsi",
                    width="large",
                ),
                "Kategori": st.column_config.TextColumn(
                    "Kategori",
                    width="medium",
                ),
                "Tipe": st.column_config.TextColumn(
                    "Tipe",
                    width="medium",
                ),
                "Jumlah": st.column_config.NumberColumn(
                    "Jumlah",
                    format="Rp%d",
                ),
            },
        )

        st.markdown(
            f"<div style='text-align:center;font-size:12px;"
            f"font-weight:700;color:#253029'>"
            f"Total {len(filtered_dataframe)} transaksi"
            f"</div>",
            unsafe_allow_html=True,
        )


# =========================================================
# EXPORT
# =========================================================
with st.container(border=True):
    export_left, export_right = st.columns([4, 1.15])

    with export_left:
        st.markdown(
            """
            <div class="section-title">
                <span class="section-number">5</span>
                📄 Export Laporan
            </div>
            <div class="export-copy">
                Unduh laporan transaksi dalam format Excel.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with export_right:
        if dataframe.empty:
            st.button(
                "📥 Download Excel",
                disabled=True,
                use_container_width=True,
            )
        else:
            excel_file = create_excel_report(
                dataframe,
                total_income,
                total_expense,
                net_result,
                expense_ratio,
            )

            st.download_button(
                "📥 Download Excel",
                data=excel_file,
                file_name=(
                    f"CatatCuanAI_{date.today().isoformat()}.xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
            )


# =========================================================
# RESET + FOOTER
# =========================================================
reset_column, _ = st.columns([1, 4])

with reset_column:
    if st.button(
        "Hapus semua data",
        use_container_width=True,
    ):
        st.session_state.transactions = []
        st.session_state.chat_history = []
        st.rerun()

st.markdown(
    """
    <div class="footer-copy">
        CatatCuan AI &nbsp; • &nbsp;
        Powered by Gemini AI &nbsp; • &nbsp;
        Made with ❤️
    </div>
    """,
    unsafe_allow_html=True,
)
