"""
dashboard.py — Halaman "Dashboard" (ringkasan/beranda).

Menampilkan hero banner, kartu ringkasan keuangan, grafik arus kas,
insight singkat, dan pratinjau transaksi terakhir. Untuk mencatat
transaksi baru, lihat pages/transaksi.py; untuk insight & chat lebih
lengkap, lihat pages/ai_insight.py & pages/ai_chat.py.
"""
import pandas as pd
import streamlit as st

from utils.formatter import format_rupiah


def metric_card(label: str, value: str, icon: str, extra: str = ""):
    st.markdown(
        f'''<div class="metric-card {extra}"><div><div class="metric-label">{label}</div>'''
        f'''<div class="metric-value">{value}</div></div><div class="metric-icon">{icon}</div></div>''',
        unsafe_allow_html=True,
    )


def render():
    st.markdown(
        '''<div class="topbar">
            <div>
                <div class="kicker">Dashboard keuangan usaha</div>
                <div class="page-title">Selamat datang, Etyka! 👋</div>
            </div>
            <div class="profile">
                <div class="avatar">👩🏻</div>
                <div class="profile-name">Etyka K.</div>
                <div>⌄</div>
            </div>
        </div>
        <div class="hero">
            <div class="hero-copy">
                <div class="eyebrow">CatatCuan AI</div>
                <div class="hero-title">Catat pemasukan & pengeluaran<span>semudah bercerita</span></div>
                <div class="hero-sub">AI membantu membaca transaksi, menyusunnya menjadi catatan keuangan, dan memberikan gambaran kondisi usaha dalam satu dashboard.</div>
            </div>
            <div class="hero-art">
                <div class="panel"></div>
                <div class="bars"><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div></div>
                <div class="robot">🤖</div>
            </div>
        </div>''',
        unsafe_allow_html=True,
    )

    transactions = st.session_state.transactions
    if transactions:
        dataframe = pd.DataFrame(transactions)
        total_income = int(dataframe.loc[dataframe["Jenis"] == "Pemasukan", "Nominal"].sum())
        total_expense = int(dataframe.loc[dataframe["Jenis"] == "Pengeluaran", "Nominal"].sum())
    else:
        dataframe = pd.DataFrame()
        total_income = total_expense = 0
    net_result = total_income - total_expense

    chart_col, summary_col = st.columns([1.3, 1], gap="large")
    with summary_col:
        st.markdown('<div class="section-title">Ringkasan Keuangan</div>', unsafe_allow_html=True)
        metric_card("Total Pemasukan", format_rupiah(total_income), "↗️")
        metric_card("Total Pengeluaran", format_rupiah(total_expense), "↘️", "negative")
        metric_card(
            "Laba Bersih" if net_result >= 0 else "Kerugian",
            format_rupiah(net_result if net_result >= 0 else abs(net_result)),
            "💰",
            "profit" if net_result >= 0 else "negative",
        )
    with chart_col:
        st.markdown('<div class="section-title">Arus Keuangan</div>', unsafe_allow_html=True)
        chart_df = pd.DataFrame(
            {"Kategori": ["Pemasukan", "Pengeluaran"], "Nominal": [total_income, total_expense]}
        ).set_index("Kategori")
        st.bar_chart(chart_df, use_container_width=True, height=260)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🧾 Transaksi Terakhir</div>', unsafe_allow_html=True)
    if transactions:
        display_df = dataframe.tail(5).iloc[::-1].copy()
        display_df.index = range(1, len(display_df) + 1)
        display_df["Nominal"] = display_df["Nominal"].apply(format_rupiah)
        st.dataframe(display_df, use_container_width=True, hide_index=False)
        st.caption("Buka halaman **Transaksi** untuk melihat & mengelola seluruh riwayat.")
    else:
        st.markdown(
            '''<div class="empty"><div class="empty-icon">🧾</div>'''
            '''<strong>Belum ada transaksi</strong><br>Buka halaman <b>Transaksi</b> untuk mencatat transaksi pertama kamu.</div>''',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="footer-note">CatatCuan AI adalah MVP. Periksa kembali hasil pencatatan sebelum mengambil keputusan keuangan.</div>',
        unsafe_allow_html=True,
    )
