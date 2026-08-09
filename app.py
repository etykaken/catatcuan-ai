import time
from pathlib import Path

import pandas as pd
import streamlit as st

from components.auth import render_auth
from components.chat import render_chat
from components.export import render_export
from components.header import render_header
from components.history import render_history
from components.insight_chart import render_insight_and_chart
from components.summary import render_summary
from components.transaction_input import render_transaction_input
from components.transaction_preview import render_transaction_preview
from utils.i18n import t

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

from services.supabase_service import (
    SupabaseServiceError,
    sign_in,
    sign_up,
)

from utils.security import redact_secret_like_strings
from utils.transactions import validate_transactions


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="CatatCuan AI",
    page_icon=(
        str(FAVICON_PATH)
        if FAVICON_PATH.exists()
        else "🤖"
    ),
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# LOAD CSS
# =========================================================

css_path = (
    Path(__file__).resolve().parent
    / "styles"
    / "main.css"
)

if css_path.exists():
    css_content = css_path.read_text(
        encoding="utf-8"
    )

    st.markdown(
        f"<style>{css_content}</style>",
        unsafe_allow_html=True,
    )


# =========================================================
# DEBUG MODE
# =========================================================

try:
    DEBUG_MODE = bool(
        st.secrets.get(
            "DEBUG_MODE",
            False,
        )
    )
except (FileNotFoundError, KeyError):
    DEBUG_MODE = False


# =========================================================
# SESSION STATE
# =========================================================

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = False

if "user" not in st.session_state:
    st.session_state.user = None

if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "pending_transactions" not in st.session_state:
    st.session_state.pending_transactions = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0.0

if "last_chat_request_time" not in st.session_state:
    st.session_state.last_chat_request_time = 0.0
    
if "language" not in st.session_state:
    st.session_state.language = "id"
    

# =========================================================
# GROQ API KEY
# =========================================================

def get_api_key() -> str | None:
    try:
        return st.secrets["GROQ_API_KEY"]

    except (FileNotFoundError, KeyError):
        st.error(
            "GROQ_API_KEY belum dipasang "
            "di Streamlit Secrets."
        )

        return None


# =========================================================
# AUTH PAGE
# =========================================================

if st.session_state.auth_mode:
    mode, email, password, submitted = render_auth()

    if submitted:
        try:

            # =================================================
            # SIGN UP
            # =================================================

            if mode == "signup":
                response = sign_up(
                    email=email,
                    password=password,
                )

                if response.session:
                    st.session_state.user = response.user
                    st.session_state.auth_mode = False

                    st.success(
                        "Akun berhasil dibuat. "
                        "Selamat datang di CatatCuan."
                    )

                    st.rerun()

                else:
                    st.success(
                        "Akun berhasil dibuat. "
                        "Silakan cek email untuk "
                        "mengonfirmasi akunmu."
                    )

            # =================================================
            # LOGIN
            # =================================================

            elif mode == "login":
                response = sign_in(
                    email=email,
                    password=password,
                )

                st.session_state.user = response.user
                st.session_state.auth_mode = False

                st.success(
                    "Berhasil masuk ke CatatCuan."
                )

                st.rerun()

        except SupabaseServiceError as error:
            st.error(
                str(error)
            )

        except Exception as error:
            st.error(
                "CatatCuan belum berhasil "
                "memproses akunmu."
            )

            if DEBUG_MODE:
                with st.expander(
                    "Detail error"
                ):
                    st.code(
                        str(error)
                    )

    st.write("")

    if st.button(
        "← Kembali ke CatatCuan",
        key="back_to_home",
    ):
        st.session_state.auth_mode = False
        st.rerun()

    # Hentikan render dashboard hanya ketika
    # user memang sedang berada di halaman auth.
    st.stop()


# =========================================================
# AUTH ENTRY BUTTON
# =========================================================

auth_column, spacer_column = st.columns(
    [1.25, 5]
)

with auth_column:

    if st.session_state.user is None:
        if st.button(
            "Masuk / Buat akun",
            key="open_auth",
            use_container_width=True,
        ):
            st.session_state.auth_mode = True
            st.rerun()

    else:
        user_email = getattr(
            st.session_state.user,
            "email",
            None,
        )

        if user_email:
            st.caption(
                f"Masuk sebagai {user_email}"
            )


# =========================================================
# HEADER
# =========================================================

render_header()


# =========================================================
# DATAFRAME
# =========================================================

if st.session_state.transactions:
    dataframe = pd.DataFrame(
        st.session_state.transactions
    )

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


# =========================================================
# FINANCIAL CALCULATION
# =========================================================

total_income = (
    int(
        dataframe.loc[
            dataframe["Tipe"] == "Pemasukan",
            "Jumlah",
        ].sum()
    )
    if not dataframe.empty
    else 0
)

total_expense = (
    int(
        dataframe.loc[
            dataframe["Tipe"] == "Pengeluaran",
            "Jumlah",
        ].sum()
    )
    if not dataframe.empty
    else 0
)

net_result = (
    total_income
    - total_expense
)

expense_ratio = (
    total_expense
    / total_income
    * 100
    if total_income > 0
    else 0.0
)


# =========================================================
# TRANSACTION INPUT + SUMMARY
# =========================================================

left_column, right_column = st.columns(
    [1, 1],
    gap="medium",
)

with left_column:
    (
        transaction_text,
        analyze_button,
    ) = render_transaction_input()

with right_column:
    render_summary(
        total_income,
        total_expense,
        net_result,
    )


# =========================================================
# ANALYZE TRANSACTIONS
# =========================================================

if analyze_button:
    now = time.time()

    if (
        now
        - st.session_state.last_request_time
        < RATE_LIMIT_SECONDS
    ):
        st.warning(
            "Tunggu beberapa detik "
            "sebelum mengirim lagi."
        )

    elif not transaction_text.strip():
        st.warning(
            "Tulis transaksi terlebih dahulu."
        )

    else:
        api_key = get_api_key()

        if api_key:
            try:
                st.session_state.last_request_time = (
                    now
                )

                with st.spinner(
                    "CatatCuan sedang "
                    "memahami ceritamu..."
                ):
                    result = analyze_transactions(
                        api_key=api_key,
                        user_input=(
                            transaction_text
                            .strip()[
                                :MAX_INPUT_LENGTH
                            ]
                        ),
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
                        "CatatCuan belum menemukan "
                        "transaksi yang bisa dicatat."
                    )

                else:
                    remaining = (
                        MAX_TOTAL_TRANSACTIONS
                        - len(
                            st.session_state.transactions
                        )
                    )

                    if remaining <= 0:
                        st.warning(
                            "Riwayat transaksi "
                            "sudah mencapai batas."
                        )

                    else:
                        st.session_state.pending_transactions = (
                            new_transactions[
                                :remaining
                            ]
                        )

                        st.rerun()

            except Exception as error:
                st.error(
                    "Transaksi gagal diproses. "
                    "Silakan coba lagi."
                )

                if DEBUG_MODE:
                    with st.expander(
                        "Detail error"
                    ):
                        st.code(
                            redact_secret_like_strings(
                                str(error),
                                api_key,
                            )
                        )


# =========================================================
# EDITABLE TRANSACTION PREVIEW
# =========================================================

if st.session_state.pending_transactions:
    (
        edited_transactions,
        save_button,
        cancel_button,
    ) = render_transaction_preview(
        st.session_state.pending_transactions
    )

    if cancel_button:
        st.session_state.pending_transactions = []
        st.rerun()

    if save_button:
        transactions_to_save = (
            edited_transactions
        )

        st.session_state.transactions.extend(
            transactions_to_save
        )

        st.session_state.pending_transactions = []

        st.success(
            f"{len(transactions_to_save)} "
            "transaksi berhasil disimpan."
        )

        st.rerun()


# =========================================================
# FINANCIAL INSIGHT + CASH FLOW
# =========================================================

render_insight_and_chart(
    dataframe,
    total_income,
    total_expense,
    net_result,
    expense_ratio,
)


# =========================================================
# CATATCUAN AI CHAT
# =========================================================

(
    question,
    ask_button,
    clear_chat_button,
) = render_chat()


if clear_chat_button:
    st.session_state.chat_history = []
    st.rerun()


if ask_button:
    now = time.time()

    if dataframe.empty:
        st.warning(
            "Tambahkan transaksi sebelum "
            "bertanya kepada CatatCuan."
        )

    elif not question.strip():
        st.warning(
            "Tulis pertanyaan terlebih dahulu."
        )

    elif (
        now
        - st.session_state.last_chat_request_time
        < RATE_LIMIT_SECONDS
    ):
        st.warning(
            "Tunggu beberapa detik "
            "sebelum bertanya lagi."
        )

    else:
        api_key = get_api_key()

        if api_key:
            try:
                st.session_state.last_chat_request_time = (
                    now
                )

                with st.spinner(
                    "CatatCuan sedang "
                    "menganalisis keuanganmu..."
                ):
                    answer = ask_financial_assistant(
                        api_key=api_key,
                        question=question.strip(),
                        transactions=(
                            st.session_state.transactions
                        ),
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
                    "CatatCuan belum berhasil "
                    "menjawab pertanyaan."
                )

                if DEBUG_MODE:
                    with st.expander(
                        "Detail error"
                    ):
                        st.code(
                            redact_secret_like_strings(
                                str(error),
                                api_key,
                            )
                        )


# =========================================================
# TRANSACTION HISTORY
# =========================================================

render_history(
    dataframe
)


# =========================================================
# EXPORT
# =========================================================

render_export(
    dataframe,
    total_income,
    total_expense,
    net_result,
    expense_ratio,
)


# =========================================================
# RESET DATA
# =========================================================

reset_column, _ = st.columns(
    [1, 4]
)

with reset_column:
    if st.button(
        "Hapus semua data",
        use_container_width=True,
        key="reset_all_data",
    ):
        st.session_state.transactions = []
        st.session_state.pending_transactions = []
        st.session_state.chat_history = []

        st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
<div class="footer-copy">
    CatatCuan AI • Catat keuangan semudah bercerita.
</div>
""",
    unsafe_allow_html=True,
)
