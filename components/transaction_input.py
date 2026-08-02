import streamlit as st

from config import MAX_INPUT_LENGTH


def render_transaction_input() -> tuple[str, bool]:
    with st.container(border=True):
        st.markdown(
            """
            <div class="section-title">
                <span class="section-number">1</span>
                ✍️ Catat Transaksi
            </div>
            <div class="section-helper">
                Tulis transaksi harian dengan bahasa alami.
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
            height=140,
            max_chars=MAX_INPUT_LENGTH,
            label_visibility="collapsed",
        )

        analyze_button = st.button(
            "✨ Analisis & Tambahkan Transaksi",
            type="primary",
            use_container_width=True,
        )

    return transaction_text, analyze_button
