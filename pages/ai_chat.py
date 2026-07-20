"""
pages/ai_chat.py — Tanya jawab bebas seputar transaksi yang sudah dicatat.
"""
import time

import streamlit as st

from services.gemini_service import ask_financial_assistant
from utils import MAX_CHAT_LENGTH, RATE_LIMIT_SECONDS
from utils.formatter import redact_secret_like_strings


def render():
    st.markdown('<div class="page-title">💬 AI Chat</div>', unsafe_allow_html=True)
    st.caption("Tanyakan apa saja berdasarkan transaksi yang sudah kamu catat.")
    st.markdown("<br>", unsafe_allow_html=True)

    if not st.session_state.transactions:
        st.markdown(
            '''<div class="empty"><div class="empty-icon">💬</div>'''
            '''<strong>Belum ada transaksi</strong><br>Catat transaksi terlebih dahulu di halaman <b>Transaksi</b> sebelum bertanya ke AI.</div>''',
            unsafe_allow_html=True,
        )
        return

    with st.container(border=True):
        s1, s2, s3 = st.columns(3)
        with s1:
            suggestion_1 = st.button("Uang saya paling banyak habis di mana?", use_container_width=True)
        with s2:
            suggestion_2 = st.button("Berapa laba saya saat ini?", use_container_width=True)
        with s3:
            suggestion_3 = st.button("Apakah kondisi keuangan saya sehat?", use_container_width=True)

        if suggestion_1:
            st.session_state.chat_question = "Uang saya paling banyak habis di mana?"
            st.session_state.chat_answer = ""
            st.rerun()
        if suggestion_2:
            st.session_state.chat_question = "Berapa laba saya saat ini?"
            st.session_state.chat_answer = ""
            st.rerun()
        if suggestion_3:
            st.session_state.chat_question = "Apakah kondisi keuangan saya sehat?"
            st.session_state.chat_answer = ""
            st.rerun()

        chat_question = st.text_input(
            "Pertanyaan kamu",
            key="chat_question",
            placeholder="Contoh: kategori pengeluaran terbesar saya apa?",
            max_chars=MAX_CHAT_LENGTH,
            label_visibility="collapsed",
        )
        ask_button = st.button("🤖 Tanya AI", type="primary", use_container_width=True)

        if ask_button:
            now = time.time()
            if now - st.session_state.last_chat_request_time < RATE_LIMIT_SECONDS:
                st.warning("Mohon tunggu beberapa detik sebelum bertanya lagi.")
            elif not chat_question.strip():
                st.warning("Tulis pertanyaan terlebih dahulu.")
            else:
                try:
                    api_key = st.secrets["GEMINI_API_KEY"]
                except (FileNotFoundError, KeyError):
                    st.error("GEMINI_API_KEY belum dipasang di Streamlit Secrets.")
                else:
                    safe_chat_question = chat_question.strip()[:MAX_CHAT_LENGTH]
                    try:
                        st.session_state.last_chat_request_time = now
                        with st.spinner("CatatCuan AI sedang menganalisis keuanganmu..."):
                            answer = ask_financial_assistant(
                                api_key=api_key,
                                question=safe_chat_question,
                                transactions=st.session_state.transactions,
                            )
                        st.session_state.chat_answer = answer
                    except Exception as error:
                        st.error("CatatCuan AI gagal menjawab. Silakan coba kembali.")
                        if st.session_state.get("debug_mode"):
                            with st.expander("Lihat detail error"):
                                st.code(redact_secret_like_strings(str(error), api_key))

        if st.session_state.chat_answer:
            st.markdown('<div class="badge">🤖 Jawaban CatatCuan AI</div>', unsafe_allow_html=True)
            # Jawaban AI ditaruh lewat st.markdown TANPA unsafe_allow_html,
            # supaya kalau ada HTML/script hasil prompt injection di
            # jawabannya, akan ikut di-escape (bukan dieksekusi).
            st.markdown(st.session_state.chat_answer)
