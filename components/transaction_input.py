import streamlit as st

from config import MAX_INPUT_LENGTH


def render_transaction_input() -> tuple[str, bool]:
    with st.container(border=True):
        st.markdown(
            """
            <div class="card-kicker">✦ &nbsp; CERITA KE CATATCUAN</div>
            <div class="input-heading">Ceritakan transaksi kamu hari ini...</div>
            <div class="card-helper">Catat keuangan semudah bercerita.</div>
            """,
            unsafe_allow_html=True,
        )
        transaction_text = st.text_area(
            "Transaction",
            placeholder="Tadi pagi beli stok gula 5 kg Rp90.000",
            height=116,
            max_chars=MAX_INPUT_LENGTH,
            label_visibility="collapsed",
            key="transaction_input_text",
        )
        st.markdown(
            """
            <div class="example-chips" aria-label="Contoh transaksi">
                <span>Jual 3 kopi</span><span>Bayar listrik</span>
                <span>Beli stok gula</span><span>＋ Lainnya</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        analyze_button = st.button(
            "➤  Catat dengan AI  ✦",
            type="primary",
            use_container_width=True,
            key="analyze_transaction_button",
        )
    return transaction_text, analyze_button
