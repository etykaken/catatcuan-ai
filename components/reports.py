import html
from collections import defaultdict

import pandas as pd
import streamlit as st

from utils.excel_report import create_excel_report


MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


def _rupiah(value: int) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}Rp{abs(value):,.0f}".replace(",", ".")


def _rows(frame: pd.DataFrame, transaction_type: str) -> list[tuple[str, int]]:
    selected = frame[frame["Tipe"] == transaction_type]
    if selected.empty:
        return []
    grouped = selected.groupby("Kategori", dropna=False)["Jumlah"].sum().sort_values(ascending=False)
    return [(str(category or "Lainnya"), int(amount)) for category, amount in grouped.items()]


def _line_items(items: list[tuple[str, int]], tone: str = "") -> str:
    if not items:
        return '<div class="report-empty">Belum ada transaksi pada periode ini.</div>'
    return "".join(
        f'<div class="report-line"><span>{html.escape(label)}</span><b class="{tone}">{_rupiah(value)}</b></div>'
        for label, value in items
    )


def _report_card(title: str, period: str, body: str, detail: str) -> str:
    return f"""<section class="report-card"><div class="report-card-head"><span class="report-card-icon">▤</span>
      <div><h3>{title}</h3><small>{html.escape(period)}</small></div></div>{body}
      <div class="report-detail">{detail} →</div></section>"""


def _profit_loss(frame: pd.DataFrame, period: str) -> str:
    income = _rows(frame, "Pemasukan")
    expense = _rows(frame, "Pengeluaran")
    total_income = sum(value for _, value in income)
    total_expense = sum(value for _, value in expense)
    net = total_income - total_expense
    body = f"""<h4>Pendapatan</h4>{_line_items(income, 'positive')}
      <div class="report-total"><span>Total Pendapatan</span><b class="positive">{_rupiah(total_income)}</b></div>
      <h4>Pengeluaran</h4>{_line_items(expense, 'negative')}
      <div class="report-total"><span>Total Pengeluaran</span><b class="negative">{_rupiah(-total_expense)}</b></div>
      <div class="report-highlight"><span>Laba Bersih</span><b class="{'positive' if net >= 0 else 'negative'}">{_rupiah(net)}</b></div>"""
    return _report_card("Laba Rugi", period, body, "Lihat detail Laba Rugi")


def _balance(frame: pd.DataFrame, period: str) -> str:
    income = int(frame.loc[frame["Tipe"] == "Pemasukan", "Jumlah"].sum()) if not frame.empty else 0
    expense = int(frame.loc[frame["Tipe"] == "Pengeluaran", "Jumlah"].sum()) if not frame.empty else 0
    cash = income - expense
    body = f"""<h4>Saldo yang tersedia</h4>
      <div class="report-line"><span>Saldo transaksi tercatat</span><b class="{'positive' if cash >= 0 else 'negative'}">{_rupiah(cash)}</b></div>
      <div class="limited-state"><strong>Neraca lengkap belum tersedia</strong><p>Data transaksi saat ini tidak mencatat piutang, persediaan, aset tetap, utang, atau modal secara terpisah.</p></div>"""
    return _report_card("Neraca", f"Per {period}", body, "Lihat detail Neraca")


def _cash_flow(frame: pd.DataFrame, period: str) -> str:
    incoming = _rows(frame, "Pemasukan")
    outgoing = _rows(frame, "Pengeluaran")
    total_in = sum(value for _, value in incoming)
    total_out = sum(value for _, value in outgoing)
    net = total_in - total_out
    body = f"""<h4>Kas Masuk</h4>{_line_items(incoming, 'positive')}
      <div class="report-total"><span>Total Kas Masuk</span><b class="positive">{_rupiah(total_in)}</b></div>
      <h4>Kas Keluar</h4>{_line_items(outgoing, 'negative')}
      <div class="report-total"><span>Total Kas Keluar</span><b class="negative">{_rupiah(-total_out)}</b></div>
      <div class="report-highlight"><span>Arus Kas Bersih</span><b class="{'positive' if net >= 0 else 'negative'}">{_rupiah(net)}</b></div>"""
    return _report_card("Arus Kas", period, body, "Lihat detail Arus Kas")


def _chart_card(all_frame: pd.DataFrame) -> str:
    monthly = defaultdict(lambda: [0, 0])
    for _, row in all_frame.iterrows():
        parsed = pd.to_datetime(row["Tanggal"], errors="coerce")
        if pd.isna(parsed):
            continue
        key = (parsed.year, parsed.month)
        monthly[key][0 if row["Tipe"] == "Pemasukan" else 1] += int(row["Jumlah"])
    points = sorted(monthly.items())[-6:]
    if not points:
        chart = '<div class="chart-limited">▥<strong>Belum cukup data</strong><span>Grafik akan muncul setelah transaksi tercatat.</span></div>'
    else:
        maximum = max(max(values) for _, values in points) or 1
        bars = "".join(
            f'<div class="chart-group"><div class="bars"><i style="height:{max(3, values[0] / maximum * 82):.0f}px"></i><i class="expense" style="height:{max(3, values[1] / maximum * 82):.0f}px"></i></div><small>{MONTHS[key[1]-1][:3]}</small></div>'
            for key, values in points
        )
        chart = f'<h4>Pendapatan vs Beban</h4><div class="chart-legend"><span>● Pendapatan</span><span>● Beban</span></div><div class="mini-chart">{bars}</div>'
    return _report_card("Grafik Ringkasan", "Data periode tersedia", chart, "Lihat analisis lengkap")


def render_reports(dataframe: pd.DataFrame, total_income: int, total_expense: int, net_result: int, expense_ratio: float) -> None:
    dated = dataframe.copy()
    dated["_date"] = pd.to_datetime(dated["Tanggal"], errors="coerce")
    periods = sorted({(d.year, d.month) for d in dated["_date"].dropna()}, reverse=True)
    if not periods:
        today = pd.Timestamp.today()
        periods = [(today.year, today.month)]
    labels = [f"{MONTHS[month - 1]} {year}" for year, month in periods]

    header_left, period_column, export_column = st.columns([4.2, 1.25, 1.55], vertical_alignment="center")
    with header_left:
        st.markdown('<div class="report-header"><h1>Laporan Keuangan <span>✦</span></h1><p>Laporan keuangan sederhana untuk memahami kondisi usaha Anda.</p></div>', unsafe_allow_html=True)
    with period_column:
        selected_label = st.selectbox("Periode laporan", labels, label_visibility="collapsed")
    year, month = periods[labels.index(selected_label)]
    period_frame = dated[(dated["_date"].dt.year == year) & (dated["_date"].dt.month == month)].drop(columns=["_date"])
    income = int(period_frame.loc[period_frame["Tipe"] == "Pemasukan", "Jumlah"].sum()) if not period_frame.empty else 0
    expense = int(period_frame.loc[period_frame["Tipe"] == "Pengeluaran", "Jumlah"].sum()) if not period_frame.empty else 0
    net = income - expense
    through_period = dated[dated["_date"] < pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthBegin(1)]
    cash_balance = int(through_period.loc[through_period["Tipe"] == "Pemasukan", "Jumlah"].sum() - through_period.loc[through_period["Tipe"] == "Pengeluaran", "Jumlah"].sum()) if not through_period.empty else 0
    with export_column:
        if dataframe.empty:
            st.button("⇩ Unduh Laporan (Excel)", disabled=True, use_container_width=True)
        else:
            export = create_excel_report(dataframe, total_income, total_expense, net_result, expense_ratio)
            st.download_button("⇩ Unduh Laporan (Excel)", export, "CatatCuan_Laporan.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    tabs = st.tabs(["Ringkasan", "Laba Rugi", "Neraca", "Arus Kas", "Catatan"])
    summary = f"""<section class="report-summary"><h2>Ringkasan Keuangan {html.escape(selected_label)}</h2><div class="summary-metrics">
      <div><span>Pendapatan</span><strong class="positive">{_rupiah(income)}</strong><i>↗</i></div>
      <div><span>Laba Bersih</span><strong class="{'positive' if net >= 0 else 'negative'}">{_rupiah(net)}</strong><i>▣</i></div>
      <div><span>Arus Kas Bersih</span><strong class="{'positive' if net >= 0 else 'negative'}">{_rupiah(net)}</strong><i>↝</i></div>
      <div><span>Saldo Kas Akhir</span><strong class="{'positive' if cash_balance >= 0 else 'negative'}">{_rupiah(cash_balance)}</strong><i>▤</i></div></div></section>"""
    with tabs[0]:
        st.markdown(summary, unsafe_allow_html=True)
        st.markdown(f'<div class="report-grid">{_profit_loss(period_frame, selected_label)}{_balance(period_frame, selected_label)}{_cash_flow(period_frame, selected_label)}{_chart_card(dataframe)}</div>', unsafe_allow_html=True)
        st.markdown('<aside class="report-note"><b>ⓘ &nbsp; Catatan Penting</b><span>Laporan ini disusun berdasarkan transaksi CatatCuan yang telah dicatat dan dikonfirmasi. Pastikan pencatatan transaksi sudah benar agar laporan tetap akurat.</span></aside>', unsafe_allow_html=True)
    with tabs[1]: st.markdown(f'<div class="report-expanded">{_profit_loss(period_frame, selected_label)}</div>', unsafe_allow_html=True)
    with tabs[2]: st.markdown(f'<div class="report-expanded">{_balance(period_frame, selected_label)}</div>', unsafe_allow_html=True)
    with tabs[3]: st.markdown(f'<div class="report-expanded">{_cash_flow(period_frame, selected_label)}</div>', unsafe_allow_html=True)
    with tabs[4]: st.info("Laporan memakai transaksi pemasukan dan pengeluaran yang telah tercatat. CatatCuan belum menyimpan klasifikasi akuntansi lengkap seperti aset, kewajiban, dan modal, sehingga Neraca ditampilkan sebagai informasi terbatas.")
