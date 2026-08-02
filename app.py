import time
from pathlib import Path

import pandas as pd
import streamlit as st

from components.chat import render_chat
from components.export import render_export
from components.header import render_header
from components.history import render_history
from components.insight_chart import render_insight_and_chart
from components.summary import render_summary
from components.transaction_input import render_transaction_input
from config import (
    FAVICON_PATH,
    MAX_INPUT_LENGTH,
    MAX_TOTAL_TRANSACTIONS,
    RATE_LIMIT_SECONDS,
)
from services.ai_service import (
    analyze_transactions,
    ask_financial_assistant,
)
from utils.security import redact_secret_like_strings
from utils.transactions import validate_transactions


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="CatatCuan AI",
    page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else "🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# LOAD CSS
# =========================================================
def load_css() -> None:
    css_path = Path(__file__).resolve().parent / "styles" / "main.css"

    if not css_path.exists():
        st.error("File styles/main.css tidak ditemukan.")
        st.stop()

    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )


# =========================================================
# SESSION STATE
# =========================================================
def initialize_session_state() -> None:
    defaults = {
        "transactions": [],
        "chat_history": [],
        "last_request_time": 0.0,
        "last_chat_request_time": 0.0,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


# =========================================================
# SETTINGS
# =========================================================
def get_debug_mode() -> bool:
    try:
        return bool(st.secrets.get("DEBUG_MODE", False))
    except (FileNotFoundError, KeyError):
        return False


def get_api_key() -> str | None:
    try:
        return st.secrets["GROQ_API_KEY"]
    except (FileNotFoundError, KeyError):
        st.error(
            "GROQ_API_KEY belum dipasang di Streamlit Secrets."
        )
        return None


# =========================================================
# DATA HELPERS
# =========================================================
def get_dataframe() -> pd.DataFrame:
    columns = [
        "Tanggal",
        "Deskripsi",
        "Kategori",
        "Tipe",
        "Jumlah",
        "Perlu Konfirmasi",
    ]

    if not st.session_state.transactions:
        return pd.DataFrame(columns=columns)

    dataframe = pd.DataFrame(st.session_state.transactions)

    for column in columns:
        if column not in dataframe.columns:
            dataframe[column] = None

    return dataframe[columns]


def calculate_summary(
    dataframe: pd.DataFrame,
) -> tuple[int, int, int, float]:
    if dataframe.empty:
        return 0, 0, 0, 0.0

    total_income = int(
        dataframe.loc[
            dataframe["Tipe"] == "Pemasukan",
            "Jumlah",
        ].sum()
    )

    total_expense = int(
        dataframe.loc[
            dataframe["Tipe"] == "Pengeluaran",
            "Jumlah",
        ].sum()
    )

    net_result = total_income - total_expense

    expense_ratio = (
        total_expense / total_income * 100
        if total_income > 0
        else 0.0
    )

    return (
        total_income,
        total_expense,
        net_result,
        expense_ratio,
    )


# =========================================================
# TRANSACTION ACTION
# =========================================================
def handle_transaction_submission(
    transaction_text: str,
    analyze_button: bool,
    debug_mode: bool,
) -> None:
    if not analyze_button:
        return

    now = time.time()

    if (
        now - st.session_state.last_request_time
        < RATE_LIMIT_SECONDS
    ):
        st.warning(
            "Tunggu beberapa detik sebelum mengirim transaksi lagi."
        )
        return

    if not transaction_text.strip():
        st.warning("Tulis transaksi terlebih dahulu.")
        return

    api_key = get_api_key()
    if not api_key:
        return

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
            return

        remaining_slots = (
            MAX_TOTAL_TRANSACTIONS
            - len(st.session_state.transactions)
        )

        if remaining_slots <= 0:
            st.warning(
                "Riwayat transaksi sudah mencapai batas maksimum."
            )
            return

        added_transactions = new_transactions[:remaining_slots]

        st.session_state.transactions.extend(
            added_transactions
        )

        st.success(
            f"{len(added_transactions)} transaksi "
            "berhasil ditambahkan."
        )
        st.rerun()

    except Exception as error:
        st.error(
            "Transaksi gagal diproses. Silakan coba lagi."
        )

        if debug_mode:
            with st.expander("Detail error"):
                st.code(
                    redact_secret_like_strings(
                        str(error),
                        api_key,
                    )
                )


# =========================================================
# CHAT ACTION
# =========================================================
def handle_chat_submission(
    question: str,
    ask_button: bool,
    clear_chat_button: bool,
    dataframe: pd.DataFrame,
    debug_mode: bool,
) -> None:
    if clear_chat_button:
        st.session_state.chat_history = []
        st.rerun()

    if not ask_button:
        return

    now = time.time()

    if dataframe.empty:
        st.warning(
            "Tambahkan transaksi sebelum bertanya kepada AI."
        )
        return

    if not question.strip():
        st.warning("Tulis pertanyaan terlebih dahulu.")
        return

    if (
        now - st.session_state.last_chat_request_time
        < RATE_LIMIT_SECONDS
    ):
        st.warning(
            "Tunggu beberapa detik sebelum bertanya lagi."
        )
        return

    api_key = get_api_key()
    if not api_key:
        return

    try:
        st.session_state.last_chat_request_time = now

        with st.spinner(
            "CatatCuan AI sedang menganalisis..."
        ):
            answer = ask_financial_assistant(
                api_key=api_key,
                question=question.strip(),
                transactions=st.session_state.transactions,
            )

        st.session_state.chat_history.extend(
            [
                {
                    "role": "user",
                    "message": question.strip(),
                },
                {
                    "role": "assistant",
                    "message": answer,
                },
            ]
        )

        st.rerun()

    except Exception as error:
        st.error(
            "CatatCuan AI gagal menjawab. Silakan coba lagi."
        )

        if debug_mode:
            with st.expander("Detail error"):
                st.code(
                    redact_secret_like_strings(
                        str(error),
                        api_key,
                    )
                )


# =========================================================
# RESET
# =========================================================
def render_reset_button() -> None:
    reset_column, _ = st.columns([1, 4])

    with reset_column:
        reset_button = st.button(
            "Hapus semua data",
            use_container_width=True,
        )

    if reset_button:
        st.session_state.transactions = []
        st.session_state.chat_history = []
        st.session_state.last_request_time = 0.0
        st.session_state.last_chat_request_time = 0.0
        st.rerun()


# =========================================================
# MAIN — SINGLE PAGE
# =========================================================
def main() -> None:
    load_css()
    initialize_session_state()

    debug_mode = get_debug_mode()

    # Semua bagian tampil dalam SATU halaman.
    render_header()

    dataframe = get_dataframe()

    (
        total_income,
        total_expense,
        net_result,
        expense_ratio,
    ) = calculate_summary(dataframe)

    input_column, summary_column = st.columns(
        [1, 1],
        gap="medium",
    )

    with input_column:
        (
            transaction_text,
            analyze_button,
        ) = render_transaction_input()

    with summary_column:
        render_summary(
            total_income,
            total_expense,
            net_result,
        )

    handle_transaction_submission(
        transaction_text=transaction_text,
        analyze_button=analyze_button,
        debug_mode=debug_mode,
    )

    # Refresh data after possible rerun.
    dataframe = get_dataframe()

    (
        total_income,
        total_expense,
        net_result,
        expense_ratio,
    ) = calculate_summary(dataframe)

    render_insight_and_chart(
        dataframe=dataframe,
        total_income=total_income,
        total_expense=total_expense,
        net_result=net_result,
        expense_ratio=expense_ratio,
    )

    (
        question,
        ask_button,
        clear_chat_button,
    ) = render_chat()

    handle_chat_submission(
        question=question,
        ask_button=ask_button,
        clear_chat_button=clear_chat_button,
        dataframe=dataframe,
        debug_mode=debug_mode,
    )

    render_history(dataframe)

    render_export(
        dataframe=dataframe,
        total_income=total_income,
        total_expense=total_expense,
        net_result=net_result,
        expense_ratio=expense_ratio,
    )

    render_reset_button()

    st.markdown(
        """
        <div class="footer-copy">
            CatatCuan AI • Powered by Groq AI • Made with ❤️
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
