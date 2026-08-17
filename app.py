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

if "language" not in st.session_state:
    st.session_state.language = "id"

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


# =========================================================
# GROQ API KEY
# =========================================================

def get_api_key() -> str | None:
    try:
        return st.secrets["GROQ_API_KEY"]

    except (FileNotFoundError, KeyError):
        st.error(
            "GROQ_API_KEY belum tersedia "
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

            # =============================================
            # SIGN UP
            # =============================================

            if mode == "signup":

                response = sign_up(
                    email=email,
                    password=password,
                )

                if response.session:

                    st.session_state.user = (
                        response.user
                    )

                    st.session_state.auth_mode = False

                    if (
                        st.session_state.language
                        == "id"
                    ):
                        st.success(
                            "Akun berhasil dibuat. "
                            "Selamat datang di CatatCuan."
                        )

                    else:
                        st.success(
                            "Your account has been created. "
                            "Welcome to CatatCuan."
                        )

                    st.rerun()

                else:

                    if (
                        st.session_state.language
                        == "id"
                    ):
                        st.success(
                            "Akun berhasil dibuat. "
                            "Silakan cek email untuk "
                            "mengonfirmasi akunmu."
                        )

                    else:
                        st.success(
                            "Your account has been created. "
                            "Please check your email "
                            "to confirm your account."
                        )

            # =============================================
            # LOGIN
            # =============================================

            elif mode == "login":

                response = sign_in(
                    email=email,
                    password=password,
                )

                st.session_state.user = (
                    response.user
                )

                st.session_state.auth_mode = False

                if (
                    st.session_state.language
                    == "id"
                ):
                    st.success(
                        "Berhasil masuk ke CatatCuan."
                    )

                else:
                    st.success(
                        "Welcome back to CatatCuan."
                    )

                st.rerun()

        except SupabaseServiceError as error:

            st.error(
                str(error)
            )

        except Exception as error:

            if (
                st.session_state.language
                == "id"
            ):
                st.error(
                    "CatatCuan belum berhasil "
                    "memproses akunmu."
                )

            else:
                st.error(
                    "CatatCuan couldn't process "
                    "your account right now."
                )

            if DEBUG_MODE:

                with st.expander(
                    "Detail error"
                ):
                    st.code(
                        str(error)
                    )

    st.write("")

    back_label = (
        "← Kembali ke CatatCuan"
        if st.session_state.language == "id"
        else "← Back to CatatCuan"
    )

    if st.button(
        back_label,
        key="back_to_home",
    ):
        st.session_state.auth_mode = False
        st.rerun()

    # Hanya stop dashboard
    # ketika user memang membuka halaman auth.
    st.stop()


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
            dataframe["Tipe"]
            == "Pemasukan",
            "Jumlah",
        ].sum()
    )
    if not dataframe.empty
    else 0
)

total_expense = (
    int(
        dataframe.loc[
            dataframe["Tipe"]
            == "Pengeluaran",
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
# TRANSACTION INPUT + PARSED PREVIEW
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
    (
        edited_transactions,
        save_button,
        cancel_button,
    ) = render_transaction_preview(
        st.session_state.pending_transactions
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

        if (
            st.session_state.language
            == "id"
        ):
            st.warning(
                "Tunggu beberapa detik "
                "sebelum mengirim lagi."
            )

        else:
            st.warning(
                "Please wait a few seconds "
                "before submitting again."
            )

    elif not transaction_text.strip():

        if (
            st.session_state.language
            == "id"
        ):
            st.warning(
                "Tulis transaksi terlebih dahulu."
            )

        else:
            st.warning(
                "Please enter a transaction first."
            )

    else:

        api_key = get_api_key()

        if api_key:

            try:

                st.session_state.last_request_time = (
                    now
                )

                spinner_text = (
                    "CatatCuan sedang "
                    "memahami ceritamu..."
                    if st.session_state.language == "id"
                    else
                    "CatatCuan is understanding "
                    "your story..."
                )

                with st.spinner(
                    spinner_text
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

                    if (
                        st.session_state.language
                        == "id"
                    ):
                        st.warning(
                            "CatatCuan belum menemukan "
                            "transaksi yang bisa dicatat."
                        )

                    else:
                        st.warning(
                            "CatatCuan couldn't find "
                            "a transaction to record."
                        )

                else:

                    remaining = (
                        MAX_TOTAL_TRANSACTIONS
                        - len(
                            st.session_state.transactions
                        )
                    )

                    if remaining <= 0:

                        if (
                            st.session_state.language
                            == "id"
                        ):
                            st.warning(
                                "Riwayat transaksi "
                                "sudah mencapai batas."
                            )

                        else:
                            st.warning(
                                "Transaction history "
                                "has reached the limit."
                            )

                    else:

                        st.session_state.pending_transactions = (
                            new_transactions[
                                :remaining
                            ]
                        )

                        st.rerun()

            except Exception as error:

                if (
                    st.session_state.language
                    == "id"
                ):
                    st.error(
                        "Transaksi gagal diproses. "
                        "Silakan coba lagi."
                    )

                else:
                    st.error(
                        "The transaction couldn't "
                        "be processed. Please try again."
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

        if (
            st.session_state.language
            == "id"
        ):

            st.success(
                f"{len(transactions_to_save)} "
                "transaksi berhasil disimpan."
            )

        else:

            st.success(
                f"{len(transactions_to_save)} "
                "transactions saved successfully."
            )

        st.rerun()


# =========================================================
# FINANCIAL SUMMARY
# =========================================================

render_summary(
    total_income,
    total_expense,
    net_result,
)


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
# HISTORY
# =========================================================

render_history(
    dataframe
)


# =========================================================
# CHAT
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

        if (
            st.session_state.language
            == "id"
        ):
            st.warning(
                "Tambahkan transaksi sebelum "
                "bertanya kepada CatatCuan."
            )

        else:
            st.warning(
                "Add a transaction before "
                "asking CatatCuan."
            )

    elif not question.strip():

        if (
            st.session_state.language
            == "id"
        ):
            st.warning(
                "Tulis pertanyaan terlebih dahulu."
            )

        else:
            st.warning(
                "Please enter a question first."
            )

    elif (
        now
        - st.session_state.last_chat_request_time
        < RATE_LIMIT_SECONDS
    ):

        if (
            st.session_state.language
            == "id"
        ):
            st.warning(
                "Tunggu beberapa detik "
                "sebelum bertanya lagi."
            )

        else:
            st.warning(
                "Please wait a few seconds "
                "before asking again."
            )

    else:

        api_key = get_api_key()

        if api_key:

            try:

                st.session_state.last_chat_request_time = (
                    now
                )

                spinner_text = (
                    "CatatCuan sedang "
                    "menganalisis keuanganmu..."
                    if st.session_state.language == "id"
                    else
                    "CatatCuan is analyzing "
                    "your finances..."
                )

                with st.spinner(
                    spinner_text
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
                            "message": (
                                question.strip()
                            ),
                        },
                        {
                            "role": "assistant",
                            "message": answer,
                        },
                    ]
                )

                st.rerun()

            except Exception as error:

                if (
                    st.session_state.language
                    == "id"
                ):
                    st.error(
                        "CatatCuan belum berhasil "
                        "menjawab pertanyaan."
                    )

                else:
                    st.error(
                        "CatatCuan couldn't answer "
                        "your question."
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

    reset_label = (
        "Hapus semua data"
        if st.session_state.language == "id"
        else "Delete all data"
    )

    if st.button(
        reset_label,
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

footer_text = (
    "CatatCuan AI • "
    "Catat keuangan semudah bercerita."
    if st.session_state.language == "id"
    else
    "CatatCuan AI • "
    "Track your finances as naturally "
    "as telling a story."
)

st.markdown(
    f"""
<div class="footer-copy">
    {footer_text}
</div>
""",
    unsafe_allow_html=True,
)
