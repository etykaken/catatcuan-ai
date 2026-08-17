import pandas as pd
import streamlit as st

from utils.insights import build_insights


def render_insight_and_chart(
    dataframe: pd.DataFrame,
    total_income: int,
    total_expense: int,
    net_result: int,
    expense_ratio: float,
) -> None:
    chart_column, insight_column = st.columns([1.45, 1], gap="medium")

    st.markdown('<div id="arus-kas"></div>', unsafe_allow_html=True)

    with chart_column:
        with st.container(border=True):
            st.markdown(
                '<div class="section-title"><span class="section-number">4</span>Arus Kas</div>',
                unsafe_allow_html=True,
            )

            chart_data = pd.DataFrame(
                {
                    "Jenis": ["Pemasukan", "Pengeluaran"],
                    "Nominal": [total_income, total_expense],
                }
            ).set_index("Jenis")

            st.bar_chart(chart_data, height=240, use_container_width=True)

    with insight_column:
        with st.container(border=True):
            st.markdown(
                """
                <div class="section-title">
                    <span class="section-number">✦</span>
                    AI Financial Insight
                </div>
                """,
                unsafe_allow_html=True,
            )

            items = build_insights(
                dataframe,
                total_income,
                total_expense,
                net_result,
                expense_ratio,
            )

            content = '<div class="insight-list">'
            for item in items:
                content += (
                    '<div class="insight-item">'
                    '<div class="insight-check">✓</div>'
                    f'<div>{item}</div>'
                    '</div>'
                )
            content += "</div>"

            st.markdown(content, unsafe_allow_html=True)
            st.caption("Insight dihitung dari transaksi yang tersimpan.")
