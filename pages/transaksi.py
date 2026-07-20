"""
pages/transaksi.py — Catat transaksi baru & lihat seluruh riwayat.
"""
import time
from datetime import date

import pandas as pd
import streamlit as st

from services.gemini_service import analyze_transactions
from utils import MAX_INPUT_LENGTH, MAX_TOTAL_TRANSACTIONS, RATE_LIMIT_SECONDS
from utils.formatter import format_rupiah, redact_secret_like_strings
from utils.parser import validate_transactions


def render():
    st.markdown('<div class="page-title">🧾 Transaksi</div>', unsafe_allow_html=True)
    st.caption("Catat transaksi usaha kamu dalam bahasa sehari-hari — AI yang akan membacanya.")
    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            '<div class="tabs"><div class="tab-active">✍️ Tulis Transaksi</div><div>📷 Upload Nota</div></div>',
            unsafe_allow_html=True,
        )
        user_input = st.text_area(
            "Ceritakan transaksi usaha kamu",
            placeholder="Contoh: Hari ini jual kopi Rp300.000, beli susu Rp80.000, dan bayar parkir Rp5.000.",
            height=138,
            max_chars=MAX_INPUT_LENGTH,
            label_visibility="collapsed",
        )
        c1, c2 = st.columns([3, 1])
        with c1:
            analyze_button = st.button("✨ Analisis & Tambahkan Transaksi", type="primary", use_container_width=True)
        with c2:
            clear_button = st.button("🗑️ Hapus Semua", use_container_width=True)

    if clear_button:
        st.session_state.transactions = []
        st.session_state.chat_question = ""
        st.session_state.chat_answer = ""
        st.rerun()

    if analyze_button:
        now = time.time()
        if now - st.session_state.last_request_time < RATE_LIMIT_SECONDS:
            st.warning("Mohon tunggu beberapa detik sebelum mengirim permintaan berikutnya.")
        elif not user_input.strip():
            st.warning("Tulis transaksi terlebih dahulu.")
        else:
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
            except (FileNotFoundError, KeyError):
                st.error("GEMINI_API_KEY belum dipasang di Streamlit Secrets.")
            else:
                try:
                    st.session_state.last_request_time = now
                    with st.spinner("CatatCuan AI sedang membaca transaksi..."):
                        result = analyze_transactions(api_key=api_key, user_input=user_input.strip()[:MAX_INPUT_LENGTH])
                    new_transactions = validate_transactions(result.get("transactions", []) if isinstance(result, dict) else [])
                    if not new_transactions:
                        st.warning("Tidak ditemukan transaksi yang dapat dicatat.")
                    else:
                        remaining = MAX_TOTAL_TRANSACTIONS - len(st.session_state.transactions)
                        if remaining <= 0:
                            st.warning(f"Riwayat transaksi sudah mencapai batas maksimum ({MAX_TOTAL_TRANSACTIONS}).")
                        else:
                            if len(new_transactions) > remaining:
                                new_transactions = new_transactions[:remaining]
                                st.warning(f"Sebagian transaksi tidak ditambahkan karena riwayat sudah mendekati batas maksimum ({MAX_TOTAL_TRANSACTIONS}).")
                            st.session_state.transactions.extend(new_transactions)
                            st.session_state.chat_answer = ""
                            st.success(f"{len(new_transactions)} transaksi berhasil ditambahkan.")
                            st.rerun()
                except Exception as error:
                    st.error("Transaksi gagal diproses. Silakan coba kembali.")
                    if st.session_state.get("debug_mode"):
                        with st.expander("Lihat detail error"):
                            st.code(redact_secret_like_strings(str(error), api_key))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Seluruh Riwayat Transaksi</div>', unsafe_allow_html=True)
    if st.session_state.transactions:
        dataframe = pd.DataFrame(st.session_state.transactions)
        display_df = dataframe.copy()
        display_df.index = display_df.index + 1
        display_df["Nominal"] = display_df["Nominal"].apply(format_rupiah)
        st.dataframe(display_df, use_container_width=True, hide_index=False)

        confirmations = int((dataframe["Perlu Konfirmasi"] == "Ya").sum())
        if confirmations:
            st.warning(f"{confirmations} transaksi perlu diperiksa kembali.")
        else:
            st.success("Semua transaksi terbaca tanpa memerlukan konfirmasi.")
    else:
        st.markdown(
            '''<div class="empty"><div class="empty-icon">🧾</div>'''
            '''<strong>Belum ada transaksi</strong><br>Catat transaksi pertama kamu melalui kolom di atas.</div>''',
            unsafe_allow_html=True,
        )
