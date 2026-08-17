import streamlit as st
from config import MAX_INPUT_LENGTH


def render_transaction_input() -> tuple[str, bool]:
    language = st.session_state.get("language", "id")
    if language == "id":
        eyebrow, title = "✦  CERITA KE CATATCUAN", "Ceritakan transaksi kamu hari ini..."
        helper, placeholder = "Catat keuangan semudah bercerita.", "Contoh: Tadi pagi beli stok gula 5 kg Rp90.000"
        button = "➤  Catat dengan AI  ✦"
    else:
        eyebrow, title = "✦  TELL CATATCUAN", "Tell us about today's transactions..."
        helper, placeholder = "Track finances as naturally as telling a story.", "Example: Bought 5 kg of sugar stock for Rp90,000"
        button = "➤  Record with AI  ✦"
    with st.container(border=True, key="transaction_input_card"):
        st.markdown('<span id="transaction-input"></span>', unsafe_allow_html=True)
        st.markdown(f'<div class="card-eyebrow">{eyebrow}</div><h2 class="card-heading">{title}</h2><p class="card-helper">{helper}</p>', unsafe_allow_html=True)
        transaction_text = st.text_area("Transaction", placeholder=placeholder, height=92, max_chars=MAX_INPUT_LENGTH, label_visibility="collapsed", key="transaction_input_text")
        chips, action = st.columns([1.9, 1], gap="small", vertical_alignment="center")
        with chips:
            st.markdown('<div class="example-chips"><span>Jual 3 kopi</span><span>Bayar listrik</span><span>Beli stok gula</span><span>＋ Lainnya</span></div>', unsafe_allow_html=True)
        with action:
            analyze_button = st.button(button, type="primary", use_container_width=True, key="analyze_transaction_button")
    return transaction_text, analyze_button
