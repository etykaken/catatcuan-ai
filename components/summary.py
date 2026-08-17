import html

import streamlit as st

from utils.formatters import format_rupiah


def _metric(title: str, value: int, icon: str, theme: str, note: str) -> str:
    return f"""
    <div class="kpi-item {theme}">
        <div class="kpi-icon">{icon}</div>
        <div><span class="kpi-label">{html.escape(title)}</span>
        <strong>{html.escape(format_rupiah(value))}</strong>
        <small>{html.escape(note)}</small></div>
    </div>"""


def render_summary(total_income: int, total_expense: int, net_result: int) -> None:
    balance_theme = "income" if net_result >= 0 else "expense"
    content = (
        _metric("PEMASUKAN", total_income, "↗", "income", "Total pemasukan")
        + _metric("PENGELUARAN", total_expense, "↘", "expense", "Total pengeluaran")
        + _metric("SALDO", net_result, "▣", balance_theme, "Total tersedia")
    )
    st.markdown(f'<section class="kpi-row">{content}</section>', unsafe_allow_html=True)
