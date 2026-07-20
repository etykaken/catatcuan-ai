"""
pages/ai_insight.py — Ringkasan kondisi keuangan & breakdown kategori.
"""
import pandas as pd
import streamlit as st

from utils.formatter import format_rupiah


def render():
    st.markdown('<div class="page-title">✨ AI Insight</div>', unsafe_allow_html=True)
    st.caption("Gambaran singkat kondisi keuangan usaha kamu berdasarkan transaksi yang sudah dicatat.")
    st.markdown("<br>", unsafe_allow_html=True)

    transactions = st.session_state.transactions
    if transactions:
        dataframe = pd.DataFrame(transactions)
        total_income = int(dataframe.loc[dataframe["Jenis"] == "Pemasukan", "Nominal"].sum())
        total_expense = int(dataframe.loc[dataframe["Jenis"] == "Pengeluaran", "Nominal"].sum())
    else:
        dataframe = pd.DataFrame()
        total_income = total_expense = 0
    net_result = total_income - total_expense
    expense_ratio = (total_expense / total_income * 100) if total_income > 0 else 0

    if not transactions:
        title, copy = "Mulai dari transaksi pertama", "Ceritakan pemasukan atau pengeluaran menggunakan bahasa sehari-hari di halaman Transaksi. Insight akan diperbarui otomatis."
    elif net_result > 0:
        title, copy = "Usaha sedang mencatat laba", f"Laba bersih saat ini {format_rupiah(net_result)}. Pengeluaran memakai {expense_ratio:.1f}% dari total pemasukan."
    elif net_result < 0:
        title, copy = "Pengeluaran perlu diperhatikan", f"Usaha mencatat kerugian {format_rupiah(abs(net_result))}. Periksa kategori pengeluaran terbesar sebelum menambah biaya berikutnya."
    else:
        title, copy = "Posisi keuangan sedang impas", "Total pemasukan dan pengeluaran sama. Tambahkan transaksi berikutnya agar pola keuangan lebih terlihat."

    st.markdown(
        f'<div class="insight"><div class="badge">🤖 AI FINANCIAL CHECK</div>'
        f'<div class="insight-title">{title}</div><div class="insight-copy">{copy}</div></div>',
        unsafe_allow_html=True,
    )

    if not dataframe.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Pengeluaran per Kategori</div>', unsafe_allow_html=True)
        expense_df = dataframe[dataframe["Jenis"] == "Pengeluaran"]
        if not expense_df.empty:
            by_category = (
                expense_df.groupby("Kategori")["Nominal"].sum().sort_values(ascending=False)
            )
            st.bar_chart(by_category, use_container_width=True, height=260)
            top_category = by_category.index[0]
            st.caption(f"Kategori pengeluaran terbesar: **{top_category}** ({format_rupiah(by_category.iloc[0])}).")
        else:
            st.caption("Belum ada transaksi pengeluaran untuk dianalisis per kategori.")
