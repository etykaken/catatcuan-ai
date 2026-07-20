"""
pages/laporan.py — Ringkasan keuangan & unduh laporan Excel.
"""
from datetime import date
from io import BytesIO

import pandas as pd
import streamlit as st

from utils.formatter import format_rupiah


def create_excel_report(dataframe, total_income, total_expense, net_result, expense_ratio) -> BytesIO:
    buffer = BytesIO()
    summary = pd.DataFrame({
        "Keterangan": [
            "Total Pemasukan", "Total Pengeluaran", "Laba/Rugi Bersih",
            "Status Keuangan", "Rasio Pengeluaran", "Jumlah Transaksi", "Tanggal Laporan",
        ],
        "Nilai": [
            total_income, total_expense, net_result,
            "Laba" if net_result > 0 else "Rugi" if net_result < 0 else "Impas",
            f"{expense_ratio:.1f}%", len(dataframe), date.today().isoformat(),
        ],
    })
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Transaksi")
        summary.to_excel(writer, index=False, sheet_name="Ringkasan Keuangan")
        ws = writer.book["Transaksi"]
        sws = writer.book["Ringkasan Keuangan"]
        for col, width in {"A": 15, "B": 18, "C": 22, "D": 40, "E": 18, "F": 20}.items():
            ws.column_dimensions[col].width = width
        sws.column_dimensions["A"].width = 25
        sws.column_dimensions["B"].width = 25
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
        for cell in sws[1]:
            cell.font = cell.font.copy(bold=True)
        for row in range(2, ws.max_row + 1):
            ws[f"E{row}"].number_format = '"Rp"#,##0'
        for cell in ("B2", "B3", "B4"):
            sws[cell].number_format = '"Rp"#,##0'
        ws.freeze_panes = "A2"
        sws.freeze_panes = "A2"
    buffer.seek(0)
    return buffer


def render():
    st.markdown('<div class="page-title">📄 Laporan</div>', unsafe_allow_html=True)
    st.caption("Ringkasan keuangan dan unduhan laporan dalam format Excel.")
    st.markdown("<br>", unsafe_allow_html=True)

    if not st.session_state.transactions:
        st.markdown(
            '''<div class="empty"><div class="empty-icon">📄</div>'''
            '''<strong>Belum ada transaksi</strong><br>Catat transaksi terlebih dahulu di halaman <b>Transaksi</b> untuk membuat laporan.</div>''',
            unsafe_allow_html=True,
        )
        return

    dataframe = pd.DataFrame(st.session_state.transactions)
    total_income = int(dataframe.loc[dataframe["Jenis"] == "Pemasukan", "Nominal"].sum())
    total_expense = int(dataframe.loc[dataframe["Jenis"] == "Pengeluaran", "Nominal"].sum())
    net_result = total_income - total_expense
    expense_ratio = (total_expense / total_income * 100) if total_income > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pemasukan", format_rupiah(total_income))
    c2.metric("Total Pengeluaran", format_rupiah(total_expense))
    c3.metric("Laba/Rugi Bersih", format_rupiah(net_result if net_result >= 0 else abs(net_result)))

    st.markdown("<br>", unsafe_allow_html=True)
    excel_buffer = create_excel_report(dataframe, total_income, total_expense, net_result, expense_ratio)
    st.download_button(
        "📥 Download Laporan Excel",
        excel_buffer,
        file_name=f"CatatCuanAI_Laporan_{date.today().isoformat()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
