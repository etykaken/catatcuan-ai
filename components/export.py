from datetime import date

import pandas as pd
import streamlit as st

from utils.excel_report import create_excel_report


def render_export(
    dataframe: pd.DataFrame,
    total_income: int,
    total_expense: int,
    net_result: int,
    expense_ratio: float,
) -> None:
    with st.container(border=True):
        left, right = st.columns([4, 1.2])

        with left:
            st.markdown(
                """
                <div class="section-title">
                    <span class="section-number">5</span>
                    📄 Export Laporan
                </div>
                <div class="section-helper">
                    Unduh transaksi dan ringkasan dalam format Excel.
                </div>
                """,
                unsafe_allow_html=True,
            )

        with right:
            if dataframe.empty:
                st.button(
                    "📥 Download Excel",
                    disabled=True,
                    use_container_width=True,
                )
            else:
                excel_file = create_excel_report(
                    dataframe,
                    total_income,
                    total_expense,
                    net_result,
                    expense_ratio,
                )

                st.download_button(
                    "📥 Download Excel",
                    data=excel_file,
                    file_name=(
                        f"CatatCuanAI_{date.today().isoformat()}.xlsx"
                    ),
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                    use_container_width=True,
                )
