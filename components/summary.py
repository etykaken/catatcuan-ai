import html
import streamlit as st
from utils.formatters import format_rupiah


def _metric(title: str, value: int, icon: str, theme: str, note: str) -> None:
    st.markdown(
        f'<div class="kpi kpi-{theme}"><div class="kpi-icon">{icon}</div><div>'
        f'<span>{html.escape(title)}</span><strong>{html.escape(format_rupiah(value))}</strong>'
        f'<small>{html.escape(note)}</small></div></div>', unsafe_allow_html=True,
    )


def render_summary(total_income: int, total_expense: int, net_result: int) -> None:
    language = st.session_state.get("language", "id")
    note = "Dari seluruh transaksi" if language == "id" else "From all transactions"
    cols = st.columns(3, gap="small")
    with cols[0]: _metric("PEMASUKAN" if language == "id" else "INCOME", total_income, "↗", "income", note)
    with cols[1]: _metric("PENGELUARAN" if language == "id" else "EXPENSES", total_expense, "↘", "expense", note)
    with cols[2]: _metric("SALDO" if language == "id" else "BALANCE", net_result, "▣", "balance", "Total tersedia" if language == "id" else "Available total")
