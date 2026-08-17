import html

import pandas as pd
import streamlit as st

from utils.formatters import format_rupiah


def render_history(dataframe: pd.DataFrame) -> None:
    with st.container(border=True):
        st.markdown('<div class="section-title history-title">TRANSAKSI TERAKHIR</div>', unsafe_allow_html=True)
        if dataframe.empty:
            st.markdown('<div class="empty-box">Belum ada transaksi. Transaksi yang disimpan akan muncul di sini.</div>', unsafe_allow_html=True)
            return

        rows = []
        for _, item in dataframe.tail(6).iloc[::-1].iterrows():
            transaction_type = str(item.get("Tipe", ""))
            expense = transaction_type == "Pengeluaran"
            amount = int(item.get("Jumlah", 0))
            sign = "−" if expense else "+"
            theme = "expense" if expense else "income"
            date = item.get("Tanggal", "")
            date_text = "" if pd.isna(date) else str(date)
            rows.append(
                f"""<div class="transaction-row">
                    <div class="transaction-arrow {theme}">{'↓' if expense else '↑'}</div>
                    <div class="transaction-description"><strong>{html.escape(str(item.get('Deskripsi', '')))}</strong></div>
                    <div><span class="category-pill {theme}">{html.escape(str(item.get('Kategori', '')))}</span></div>
                    <div class="transaction-type">{html.escape(transaction_type)}</div>
                    <div class="transaction-date">{html.escape(date_text)}</div>
                    <strong class="transaction-amount {theme}">{sign}{html.escape(format_rupiah(amount))}</strong>
                </div>"""
            )
        st.markdown(
            '<div class="transaction-head"><span></span><span>DESKRIPSI</span><span>KATEGORI</span><span>JENIS</span><span>WAKTU</span><span>JUMLAH</span></div>'
            + "".join(rows),
            unsafe_allow_html=True,
        )
