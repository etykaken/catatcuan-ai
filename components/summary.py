import html
from datetime import datetime

import streamlit as st

from utils.formatters import format_rupiah


def _metric_card(
    title: str,
    value: str,
    icon: str,
    theme: str,
) -> None:
    st.markdown(
        f"""
        <div class="metric-card metric-{theme}">
            <div class="metric-title">{html.escape(title)}</div>
            <div class="metric-value">{html.escape(value)}</div>
            <div class="metric-icon">{icon}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary(
    total_income: int,
    total_expense: int,
    net_result: int,
) -> None:
    with st.container(border=True):
        st.markdown(
            """
            <div class="section-title">
                <span class="section-number">3</span>
                Ringkasan Keuangan
            </div>
            """,
            unsafe_allow_html=True,
        )

        columns = st.columns(3, gap="small")

        with columns[0]:
            _metric_card(
                "Pemasukan",
                format_rupiah(total_income),
                "↑",
                "green",
            )

        with columns[1]:
            _metric_card(
                "Pengeluaran",
                format_rupiah(total_expense),
                "↓",
                "orange",
            )

        with columns[2]:
            _metric_card(
                "Laba Bersih" if net_result >= 0 else "Kerugian",
                format_rupiah(abs(net_result)),
                "⌁",
                "green" if net_result >= 0 else "orange",
            )

        st.caption(
            f"Update terakhir: {datetime.now().strftime('%d %b %Y, %H:%M')}"
        )
