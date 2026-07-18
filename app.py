import re
import time
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from services.gemini_service import (
    analyze_transactions,
    ask_financial_assistant,
)


# ── Konfigurasi & Konstanta Keamanan ────────────────────────────────
MAX_INPUT_LENGTH = 1000
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
LOGO_PATH = ASSETS_DIR / "logo.png"
FAVICON_PATH = ASSETS_DIR / "favicon.png"


# Mode debug hanya aktif jika diset melalui Streamlit Secrets.
try:
    DEBUG_MODE = bool(
        st.secrets.get("DEBUG_MODE", False)
    )
except (FileNotFoundError, KeyError):
    DEBUG_MODE = False


def resolve_date(value: str) -> str:
    """Mengubah tanggal relatif dari AI menjadi tanggal aktual."""

    today = date.today()
    normalized_value = str(value).strip().upper()

    if normalized_value == "TODAY":
        return today.isoformat()

    if normalized_value == "YESTERDAY":
        return (
            today - timedelta(days=1)
        ).isoformat()

    if normalized_value == "TOMORROW":
        return (
            today + timedelta(days=1)
        ).isoformat()

    candidate = str(value).strip()

    if ISO_DATE_PATTERN.match(candidate):
        try:
            date.fromisoformat(candidate)
            return candidate
        except ValueError:
            pass

    return today.isoformat()


def format_rupiah(value: int | float) -> str:
    """Mengubah angka menjadi format Rupiah."""

    return f"Rp{value:,.0f}".replace(",", ".")


def coerce_amount(raw_amount) -> int | None:
    """Mengonversi nominal menjadi integer secara aman."""

    if isinstance(raw_amount, bool):
        return None

    if isinstance(raw_amount, int):
        return raw_amount

    if isinstance(raw_amount, float):
        if raw_amount.is_integer():
            return int(raw_amount)

        return None

    if isinstance(raw_amount, str):
        cleaned = (
            raw_amount
            .strip()
            .replace(".", "")
            .replace(",", "")
        )

        if cleaned.isdigit():
            return int(cleaned)

    return None


def sanitize_text_field(
    value,
    max_length: int,
) -> str:
    """Membersihkan teks bebas dan membatasi panjang."""

    text = str(value).strip()

    text = "".join(
        character
        for character in text
        if character.isprintable()
        or character == "\n"
    )

    return text[:max_length]


def sanitize_excel_cell(text: str) -> str:
    """Mencegah formula injection pada file Excel."""

    text = str(text)

    if text.startswith(
        FORMULA_TRIGGER_CHARS
    ):
        text = "'" + text

    return text


def validate_transactions(
    raw_transactions: list,
) -> list:
    """Memeriksa hasil AI sebelum masuk riwayat."""

    validated_transactions = []

    if not isinstance(
        raw_transactions,
        list,
    ):
        return validated_transactions

    for item in raw_transactions[
        :MAX_TRANSACTIONS_PER_REQUEST
    ]:
        if not isinstance(item, dict):
            continue

        transaction_type = item.get("type")

        if transaction_type not in {
            "income",
            "expense",
        }:
            continue

        amount = coerce_amount(
            item.get("amount")
        )

        if (
            amount is None
            or amount <= 0
            or amount > MAX_AMOUNT
        ):
            continue

        category = sanitize_text_field(
            item.get("category", ""),
            60,
        )

        description = sanitize_text_field(
            item.get("description", ""),
            120,
        )

        validated_transactions.append(
            {
                "Tanggal": resolve_date(
                    item.get(
                        "date",
                        "TODAY",
                    )
                ),
                "Jenis": (
                    "Pemasukan"
                    if transaction_type == "income"
                    else "Pengeluaran"
                ),
                "Kategori": sanitize_excel_cell(
                    category
                ),
                "Keterangan": sanitize_excel_cell(
                    description
                ),
                "Nominal": amount,
                "Perlu Konfirmasi": (
                    "Ya"
                    if item.get(
                        "requires_confirmation",
                        False,
                    )
                    else "Tidak"
                ),
            }
        )

    return validated_transactions


def redact_secret_like_strings(
    text: str,
    api_key: str | None = None,
) -> str:
    """Menyensor string yang menyerupai API key."""

    if api_key:
        text = text.replace(
            api_key,
            "[REDACTED]",
        )

    return SECRET_LIKE_PATTERN.sub(
        "[REDACTED]",
        text,
    )


def create_excel_report(
    dataframe: pd.DataFrame,
    total_income: int,
    total_expense: int,
    net_result: int,
    expense_ratio: float,
) -> BytesIO:
    """Membuat laporan Excel transaksi dan ringkasan."""

    excel_buffer = BytesIO()

    financial_status = (
        "Laba"
        if net_result > 0
        else "Rugi"
        if net_result < 0
        else "Impas"
    )

    summary_dataframe = pd.DataFrame(
        {
            "Keterangan": [
                "Total Pemasukan",
                "Total Pengeluaran",
                "Laba/Rugi Bersih",
                "Status Keuangan",
                "Rasio Pengeluaran",
                "Jumlah Transaksi",
                "Tanggal Laporan",
            ],
            "Nilai": [
                total_income,
                total_expense,
                net_result,
                financial_status,
                f"{expense_ratio:.1f}%",
                len(dataframe),
                date.today().isoformat(),
            ],
        }
    )

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl",
    ) as writer:
        dataframe.to_excel(
            writer,
            index=False,
            sheet_name="Transaksi",
        )

        summary_dataframe.to_excel(
            writer,
            index=False,
            sheet_name="Ringkasan Keuangan",
        )

        workbook = writer.book

        transaction_sheet = workbook[
            "Transaksi"
        ]

        summary_sheet = workbook[
            "Ringkasan Keuangan"
        ]

        transaction_widths = {
            "A": 15,
            "B": 18,
            "C": 22,
            "D": 40,
            "E": 18,
            "F": 20,
        }

        for (
            column,
            width,
        ) in transaction_widths.items():
            transaction_sheet.column_dimensions[
                column
            ].width = width

        summary_sheet.column_dimensions[
            "A"
        ].width = 25

        summary_sheet.column_dimensions[
            "B"
        ].width = 25

        for cell in transaction_sheet[1]:
            cell.font = cell.font.copy(
                bold=True
            )

        for cell in summary_sheet[1]:
            cell.font = cell.font.copy(
                bold=True
            )

        for row in range(
            2,
            transaction_sheet.max_row + 1,
        ):
            transaction_sheet[
                f"E{row}"
            ].number_format = '"Rp"#,##0'

        summary_sheet[
            "B2"
        ].number_format = '"Rp"#,##0'

        summary_sheet[
            "B3"
        ].number_format = '"Rp"#,##0'

        summary_sheet[
            "B4"
        ].number_format = '"Rp"#,##0'

        transaction_sheet.freeze_panes = "A2"
        summary_sheet.freeze_panes = "A2"

    excel_buffer.seek(0)

    return excel_buffer


# ── Konfigurasi Halaman ──────────────────────────────────────────────
st.set_page_config(
    page_title="CatatCuan AI",
    page_icon=(
        str(FAVICON_PATH)
        if FAVICON_PATH.exists()
        else "💰"
    ),
    layout="wide",
)


# ── CSS Tampilan ─────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .stApp {
        background:
            linear-gradient(
                180deg,
                #F2FAF5 0%,
                #FFFFFF 42%,
                #F7F9F8 100%
            );
    }

    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    [data-testid="stImage"] {
        margin-bottom: -10px;
    }

    .stCaption {
        font-size: 16px;
        color: #52616B;
    }

    [data-testid="stAlert"] {
        border-radius: 14px;
        border: 1px solid #DCEFE4;
    }

    .stTextArea textarea {
        border-radius: 16px;
        border: 1px solid #CBDDD2;
        background-color: #FFFFFF;
        font-size: 16px;
        padding: 16px;
    }

    .stTextArea textarea:focus {
        border-color: #1F8A5B;
        box-shadow:
            0 0 0 2px
            rgba(31, 138, 91, 0.15);
    }

    .stTextInput input {
        border-radius: 12px;
        min-height: 48px;
        border: 1px solid #CBDDD2;
        background-color: #FFFFFF;
    }

    .stTextInput input:focus {
        border-color: #1F8A5B;
        box-shadow:
            0 0 0 2px
            rgba(31, 138, 91, 0.15);
    }

    .stButton button[kind="primary"] {
        background:
            linear-gradient(
                90deg,
                #176B46,
                #219A65
            );
        color: white;
        border: none;
        border-radius: 12px;
        min-height: 48px;
        font-weight: 700;
        font-size: 16px;
    }

    .stButton button[kind="primary"]:hover {
        background: #145A3C;
        color: white;
    }

    .stButton button:not([kind="primary"]) {
        border-radius: 12px;
        min-height: 44px;
        border: 1px solid #D7E2DB;
        background-color: #FFFFFF;
    }

    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2EBE5;
        padding: 20px;
        border-radius: 16px;
        box-shadow:
            0 6px 20px
            rgba(30, 70, 50, 0.06);
    }

    [data-testid="stMetricLabel"] {
        color: #66756D;
        font-size: 14px;
    }

    [data-testid="stMetricValue"] {
        color: #163D2B;
        font-weight: 800;
    }

    [data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #E1E8E4;
    }

    h1, h2, h3 {
        color: #173D2C;
        font-weight: 800;
    }

    .stDownloadButton button {
        background-color: #173D2C;
        color: #FFFFFF;
        border-radius: 12px;
        min-height: 48px;
        border: none;
        font-weight: 700;
    }

    .stDownloadButton button:hover {
        background-color: #0F2D20;
        color: #FFFFFF;
    }

    .chat-answer {
        background: #FFFFFF;
        border: 1px solid #DCE9E1;
        border-radius: 16px;
        padding: 20px 22px;
        box-shadow:
            0 6px 20px
            rgba(30, 70, 50, 0.06);
        margin-top: 12px;
        margin-bottom: 20px;
    }

    .chat-answer-title {
        color: #176B46;
        font-size: 16px;
        font-weight: 800;
        margin-bottom: 8px;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Session State ────────────────────────────────────────────────────
if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0.0

if "last_chat_request_time" not in st.session_state:
    st.session_state.last_chat_request_time = 0.0

if "chat_question" not in st.session_state:
    st.session_state.chat_question = ""

if "chat_answer" not in st.session_state:
    st.session_state.chat_answer = ""


# ── Header ───────────────────────────────────────────────────────────
if LOGO_PATH.exists():
    st.image(
        str(LOGO_PATH),
        width=380,
    )
else:
    st.title("CatatCuan AI")

st.caption(
    "Catat pemasukan dan pengeluaran usaha "
    "semudah bercerita."
)

st.info(
    "Contoh: Hari ini jual kopi Rp300.000, "
    "beli susu Rp80.000, dan bayar parkir Rp5.000."
)


# ── Input Transaksi ──────────────────────────────────────────────────
user_input = st.text_area(
    "Ceritakan transaksi usaha kamu",
    placeholder=(
        "Tulis pemasukan dan pengeluaran "
        "menggunakan bahasa sehari-hari..."
    ),
    height=150,
    max_chars=MAX_INPUT_LENGTH,
)


button_column_1, button_column_2 = st.columns(
    [3, 1]
)

with button_column_1:
    analyze_button = st.button(
        "✨ Analisis dan Tambahkan Transaksi",
        type="primary",
        use_container_width=True,
    )

with button_column_2:
    clear_button = st.button(
        "🗑️ Hapus Semua",
        use_container_width=True,
    )


if clear_button:
    st.session_state.transactions = []
    st.session_state.chat_question = ""
    st.session_state.chat_answer = ""
    st.rerun()


# ── Proses Analisis Transaksi ────────────────────────────────────────
if analyze_button:
    now = time.time()

    seconds_since_last_request = (
        now
        - st.session_state.last_request_time
    )

    if (
        seconds_since_last_request
        < RATE_LIMIT_SECONDS
    ):
        st.warning(
            "Mohon tunggu beberapa detik sebelum "
            "mengirim permintaan berikutnya."
        )

    elif not user_input.strip():
        st.warning(
            "Tulis transaksi terlebih dahulu."
        )

    else:
        try:
            api_key = st.secrets[
                "GEMINI_API_KEY"
            ]

        except (
            FileNotFoundError,
            KeyError,
        ):
            st.error(
                "GEMINI_API_KEY belum dipasang "
                "di Streamlit Secrets."
            )

        else:
            safe_user_input = (
                user_input
                .strip()
                [:MAX_INPUT_LENGTH]
            )

            try:
                st.session_state.last_request_time = (
                    now
                )

                with st.spinner(
                    "CatatCuan AI sedang "
                    "membaca transaksi..."
                ):
                    result = analyze_transactions(
                        api_key=api_key,
                        user_input=safe_user_input,
                    )

                new_transactions = (
                    validate_transactions(
                        result.get(
                            "transactions",
                            [],
                        )
                        if isinstance(
                            result,
                            dict,
                        )
                        else []
                    )
                )

                if not new_transactions:
                    st.warning(
                        "Tidak ditemukan transaksi "
                        "yang dapat dicatat."
                    )

                else:
                    remaining_capacity = (
                        MAX_TOTAL_TRANSACTIONS
                        - len(
                            st.session_state
                            .transactions
                        )
                    )

                    if remaining_capacity <= 0:
                        st.warning(
                            "Riwayat transaksi sudah "
                            "mencapai batas maksimum "
                            f"({MAX_TOTAL_TRANSACTIONS}). "
                            "Silakan unduh laporan lalu "
                            "hapus riwayat."
                        )

                    else:
                        if (
                            len(new_transactions)
                            > remaining_capacity
                        ):
                            new_transactions = (
                                new_transactions[
                                    :remaining_capacity
                                ]
                            )

                            st.warning(
                                "Sebagian transaksi tidak "
                                "ditambahkan karena riwayat "
                                "sudah mendekati batas "
                                f"maksimum "
                                f"({MAX_TOTAL_TRANSACTIONS})."
                            )

                        st.session_state.transactions.extend(
                            new_transactions
                        )

                        st.session_state.chat_answer = ""

                        st.success(
                            f"{len(new_transactions)} "
                            "transaksi berhasil "
                            "ditambahkan."
                        )

            except Exception as error:
                st.error(
                    "Transaksi gagal diproses. "
                    "Silakan coba kembali."
                )

                if DEBUG_MODE:
                    with st.expander(
                        "Lihat detail error"
                    ):
                        st.code(
                            redact_secret_like_strings(
                                str(error),
                                api_key,
                            )
                        )


# ── Dashboard & Laporan ──────────────────────────────────────────────
if st.session_state.transactions:
    dataframe = pd.DataFrame(
        st.session_state.transactions
    )

    total_income = int(
        dataframe.loc[
            dataframe["Jenis"]
            == "Pemasukan",
            "Nominal",
        ].sum()
    )

    total_expense = int(
        dataframe.loc[
            dataframe["Jenis"]
            == "Pengeluaran",
            "Nominal",
        ].sum()
    )

    net_result = (
        total_income
        - total_expense
    )

    if total_income > 0:
        expense_ratio = (
            total_expense
            / total_income
        ) * 100
    else:
        expense_ratio = 0


    st.divider()

    st.subheader(
        "📊 Ringkasan Keuangan"
    )

    (
        metric_column_1,
        metric_column_2,
        metric_column_3,
    ) = st.columns(3)

    metric_column_1.metric(
        "Total Pemasukan",
        format_rupiah(
            total_income
        ),
    )

    metric_column_2.metric(
        "Total Pengeluaran",
        format_rupiah(
            total_expense
        ),
    )

    if net_result > 0:
        metric_column_3.metric(
            "Laba Bersih",
            format_rupiah(
                net_result
            ),
        )

    elif net_result < 0:
        metric_column_3.metric(
            "Kerugian",
            format_rupiah(
                abs(net_result)
            ),
        )

    else:
        metric_column_3.metric(
            "Laba/Rugi",
            "Impas",
        )


    st.subheader(
        "💡 Insight Keuangan"
    )

    if net_result > 0:
        st.success(
            "Usaha mencatat laba bersih "
            f"sebesar "
            f"{format_rupiah(net_result)}."
        )

    elif net_result < 0:
        st.warning(
            "Usaha mencatat kerugian "
            f"sebesar "
            f"{format_rupiah(abs(net_result))}."
        )

    else:
        st.info(
            "Total pemasukan dan pengeluaran "
            "sama. Kondisi keuangan sedang "
            "impas."
        )

    if total_income > 0:
        st.write(
            "Pengeluaran menggunakan "
            f"{expense_ratio:.1f}% dari "
            "total pemasukan."
        )

    elif total_expense > 0:
        st.write(
            "Belum ada pemasukan yang "
            "tercatat, tetapi sudah terdapat "
            "pengeluaran."
        )


    st.subheader(
        "🧾 Riwayat Transaksi"
    )

    display_dataframe = (
        dataframe.copy()
    )

    display_dataframe.index = (
        display_dataframe.index + 1
    )

    display_dataframe["Nominal"] = (
        display_dataframe[
            "Nominal"
        ].apply(
            format_rupiah
        )
    )

    st.dataframe(
        display_dataframe,
        use_container_width=True,
        hide_index=False,
    )


    confirmation_count = int(
        (
            dataframe[
                "Perlu Konfirmasi"
            ]
            == "Ya"
        ).sum()
    )

    if confirmation_count > 0:
        st.warning(
            f"{confirmation_count} transaksi "
            "perlu diperiksa kembali."
        )

    else:
        st.success(
            "Semua transaksi berhasil dibaca "
            "tanpa memerlukan konfirmasi."
        )


    # ── Download Excel ───────────────────────────────────────────────
    excel_buffer = create_excel_report(
        dataframe=dataframe,
        total_income=total_income,
        total_expense=total_expense,
        net_result=net_result,
        expense_ratio=expense_ratio,
    )

    st.download_button(
        label=(
            "📥 Download Laporan "
            "Keuangan Excel"
        ),
        data=excel_buffer,
        file_name=(
            f"CatatCuanAI_Laporan_"
            f"{date.today().isoformat()}"
            f".xlsx"
        ),
        mime=(
            "application/vnd."
            "openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True,
    )


    # ── AI Finance Chat ──────────────────────────────────────────────
    st.divider()

    st.subheader(
        "💬 Tanya CatatCuan AI"
    )

    st.caption(
        "Tanyakan apa saja berdasarkan "
        "transaksi yang sudah kamu catat."
    )

    (
        suggestion_column_1,
        suggestion_column_2,
        suggestion_column_3,
    ) = st.columns(3)

    with suggestion_column_1:
        suggestion_1 = st.button(
            "Uang saya paling banyak "
            "habis di mana?",
            use_container_width=True,
        )

    with suggestion_column_2:
        suggestion_2 = st.button(
            "Berapa laba saya "
            "saat ini?",
            use_container_width=True,
        )

    with suggestion_column_3:
        suggestion_3 = st.button(
            "Apakah kondisi keuangan "
            "saya sehat?",
            use_container_width=True,
        )


    if suggestion_1:
        st.session_state.chat_question = (
            "Uang saya paling banyak "
            "habis di mana?"
        )
        st.session_state.chat_answer = ""
        st.rerun()

    if suggestion_2:
        st.session_state.chat_question = (
            "Berapa laba saya saat ini?"
        )
        st.session_state.chat_answer = ""
        st.rerun()

    if suggestion_3:
        st.session_state.chat_question = (
            "Apakah kondisi keuangan "
            "saya sehat?"
        )
        st.session_state.chat_answer = ""
        st.rerun()


    chat_question = st.text_input(
        "Pertanyaan kamu",
        key="chat_question",
        placeholder=(
            "Contoh: kategori pengeluaran "
            "terbesar saya apa?"
        ),
        max_chars=MAX_CHAT_LENGTH,
    )

    ask_button = st.button(
        "🤖 Tanya AI",
        type="primary",
        use_container_width=True,
    )


    if ask_button:
        now = time.time()

        seconds_since_last_chat = (
            now
            - st.session_state
            .last_chat_request_time
        )

        if (
            seconds_since_last_chat
            < RATE_LIMIT_SECONDS
        ):
            st.warning(
                "Mohon tunggu beberapa detik "
                "sebelum bertanya lagi."
            )

        elif not chat_question.strip():
            st.warning(
                "Tulis pertanyaan terlebih "
                "dahulu."
            )

        else:
            try:
                api_key = st.secrets[
                    "GEMINI_API_KEY"
                ]

            except (
                FileNotFoundError,
                KeyError,
            ):
                st.error(
                    "GEMINI_API_KEY belum "
                    "dipasang di Streamlit "
                    "Secrets."
                )

            else:
                safe_chat_question = (
                    chat_question
                    .strip()
                    [:MAX_CHAT_LENGTH]
                )

                try:
                    st.session_state.last_chat_request_time = (
                        now
                    )

                    with st.spinner(
                        "CatatCuan AI sedang "
                        "menganalisis keuanganmu..."
                    ):
                        answer = (
                            ask_financial_assistant(
                                api_key=api_key,
                                question=(
                                    safe_chat_question
                                ),
                                transactions=(
                                    st.session_state
                                    .transactions
                                ),
                            )
                        )

                    st.session_state.chat_answer = (
                        answer
                    )

                except Exception as error:
                    st.error(
                        "CatatCuan AI gagal "
                        "menjawab. Silakan coba "
                        "kembali."
                    )

                    if DEBUG_MODE:
                        with st.expander(
                            "Lihat detail error"
                        ):
                            st.code(
                                redact_secret_like_strings(
                                    str(error),
                                    api_key,
                                )
                            )


    if st.session_state.chat_answer:
        st.markdown(
            """
            <div class="chat-answer">
                <div class="chat-answer-title">
                    🤖 Jawaban CatatCuan AI
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            st.session_state.chat_answer
        )


else:
    st.markdown("---")

    st.info(
        "Belum ada transaksi dalam riwayat. "
        "Masukkan transaksi pertama kamu "
        "di atas."
    )


# ── Footer ───────────────────────────────────────────────────────────
st.divider()

st.caption(
    "CatatCuan AI adalah MVP. "
    "Periksa kembali hasil pencatatan "
    "sebelum mengambil keputusan keuangan."
)
