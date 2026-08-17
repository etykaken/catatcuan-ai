import html
import pandas as pd
import streamlit as st
from utils.formatters import format_rupiah


def render_history(dataframe: pd.DataFrame) -> None:
    language = st.session_state.get("language", "id")
    with st.container(border=True, key="history_card"):
        st.markdown('<div class="section-heading">TRANSAKSI TERAKHIR</div>' if language == "id" else '<div class="section-heading">RECENT TRANSACTIONS</div>', unsafe_allow_html=True)
        if dataframe.empty:
            st.markdown('<div class="history-empty"><span>▤</span><strong>Belum ada transaksi</strong><small>Transaksi yang sudah disimpan akan tampil di sini.</small></div>' if language == "id" else '<div class="history-empty"><span>▤</span><strong>No transactions yet</strong><small>Saved transactions will appear here.</small></div>', unsafe_allow_html=True)
            return
        rows = '<div class="transaction-table"><div class="transaction-head"><span></span><span>DESKRIPSI</span><span>KATEGORI</span><span>JENIS</span><span>WAKTU</span><span>JUMLAH</span></div>'
        for _, item in dataframe.tail(6).iloc[::-1].iterrows():
            income = item["Tipe"] == "Pemasukan"
            theme, arrow, sign = ("income", "↑", "+") if income else ("expense", "↓", "−")
            amount = format_rupiah(abs(int(item["Jumlah"])))
            rows += f'<div class="transaction-row"><span class="row-icon {theme}">{arrow}</span><strong>{html.escape(str(item["Deskripsi"]))}</strong><span><b class="category {theme}">{html.escape(str(item["Kategori"]))}</b></span><span>{html.escape(str(item["Tipe"]))}</span><span>{html.escape(str(item["Tanggal"]))}</span><strong class="amount {theme}">{sign}{amount}</strong></div>'
        st.markdown(rows + '</div>', unsafe_allow_html=True)
