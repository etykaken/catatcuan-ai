from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from utils.insights import build_insights


def _seven_day_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    end = datetime.now().date()
    days = [end - timedelta(days=i) for i in range(6, -1, -1)]
    result = pd.DataFrame(0, index=pd.to_datetime(days), columns=["Pemasukan", "Pengeluaran"])
    if dataframe.empty:
        return result
    dates = pd.to_datetime(dataframe["Tanggal"], errors="coerce").dt.normalize()
    for kind in result.columns:
        subset = dataframe.loc[dataframe["Tipe"] == kind].copy()
        subset["_date"] = dates[dataframe["Tipe"] == kind]
        totals = subset.groupby("_date")["Jumlah"].sum()
        result[kind] = totals.reindex(result.index, fill_value=0)
    return result


def render_insight_and_chart(dataframe: pd.DataFrame, total_income: int, total_expense: int, net_result: int, expense_ratio: float) -> None:
    language = st.session_state.get("language", "id")
    chart_column, insight_column = st.columns([1.5, 1], gap="small")
    with chart_column:
        with st.container(border=True, key="cashflow_card"):
            st.markdown('<div class="section-heading">ARUS KAS 7 HARI TERAKHIR <span><i class="legend-income"></i>Pemasukan &nbsp;&nbsp; <i class="legend-expense"></i>Pengeluaran</span></div>', unsafe_allow_html=True)
            chart_data = _seven_day_data(dataframe)
            if dataframe.empty:
                st.markdown('<div class="chart-empty"><span>⌁</span>Belum ada data arus kas dalam 7 hari terakhir.</div>' if language == "id" else '<div class="chart-empty"><span>⌁</span>No cash-flow data for the last 7 days.</div>', unsafe_allow_html=True)
            else:
                st.line_chart(chart_data, color=["#16a34a", "#ef4444"], height=225, use_container_width=True)
    with insight_column:
        with st.container(border=True, key="insight_card"):
            st.markdown('<div class="section-heading green">✦ &nbsp; INSIGHT DARI AI</div>', unsafe_allow_html=True)
            items = build_insights(dataframe, total_income, total_expense, net_result, expense_ratio)
            if dataframe.empty:
                st.markdown('<div class="insight-empty"><div>✦</div><strong>Insight menunggu datamu</strong><p>Simpan transaksi pertama untuk mendapatkan analisis keuangan.</p></div>' if language == "id" else '<div class="insight-empty"><div>✦</div><strong>Insights are waiting for your data</strong><p>Save your first transaction to get a financial analysis.</p></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="primary-insight">{items[0]}</div><p class="supporting-insight">{items[1]}</p><div class="recommendation"><b>💡 REKOMENDASI</b><br>{items[2]}</div>', unsafe_allow_html=True)
