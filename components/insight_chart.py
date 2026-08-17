import pandas as pd
import streamlit as st

from utils.insights import build_insights


def _cash_flow_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty or "Tanggal" not in dataframe.columns:
        return pd.DataFrame(columns=["Pemasukan", "Pengeluaran"])
    working = dataframe.copy()
    working["Tanggal"] = pd.to_datetime(working["Tanggal"], errors="coerce")
    working = working.dropna(subset=["Tanggal"])
    if working.empty:
        return pd.DataFrame(columns=["Pemasukan", "Pengeluaran"])
    working["Hari"] = working["Tanggal"].dt.normalize()
    pivot = working.pivot_table(index="Hari", columns="Tipe", values="Jumlah", aggfunc="sum", fill_value=0)
    end = working["Hari"].max()
    days = pd.date_range(end=end, periods=7, freq="D")
    return pivot.reindex(days, fill_value=0).reindex(columns=["Pemasukan", "Pengeluaran"], fill_value=0)


def render_insight_and_chart(
    dataframe: pd.DataFrame,
    total_income: int,
    total_expense: int,
    net_result: int,
    expense_ratio: float,
) -> None:
    chart_column, insight_column = st.columns([1.5, 1], gap="medium")
    with chart_column:
        with st.container(border=True):
            st.markdown('<div class="section-title">ARUS KAS 7 HARI TERAKHIR</div>', unsafe_allow_html=True)
            chart_data = _cash_flow_data(dataframe)
            if chart_data.empty:
                st.markdown('<div class="chart-empty">Grafik akan tampil setelah transaksi bertanggal tersimpan.</div>', unsafe_allow_html=True)
            else:
                st.line_chart(chart_data, color=["#16a34a", "#ff3b43"], height=225, use_container_width=True)

    with insight_column:
        with st.container(border=True):
            st.markdown('<div class="card-kicker">✦ &nbsp; INSIGHT DARI AI</div>', unsafe_allow_html=True)
            items = build_insights(dataframe, total_income, total_expense, net_result, expense_ratio)
            content = "".join(f'<div class="insight-item"><div class="insight-check">↗</div><div>{item}</div></div>' for item in items)
            st.markdown(f'<div class="insight-list">{content}</div>', unsafe_allow_html=True)
            if not dataframe.empty:
                st.markdown('<div class="recommendation"><b>💡 &nbsp; REKOMENDASI</b><span>Insight dihitung dari transaksi yang tersimpan.</span></div>', unsafe_allow_html=True)
