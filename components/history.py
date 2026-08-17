import pandas as pd
import streamlit as st


def render_history(dataframe: pd.DataFrame) -> None:
    st.markdown('<div id="riwayat"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        header_left, header_right = st.columns([4, 1])

        with header_left:
            st.markdown(
                """
                <div class="section-title">
                    <span class="section-number">5</span>
                    Transaksi Terbaru
                </div>
                """,
                unsafe_allow_html=True,
            )

        with header_right:
            transaction_filter = st.selectbox(
                "Filter",
                ["Semua", "Pemasukan", "Pengeluaran"],
                label_visibility="collapsed",
            )

        if dataframe.empty:
            st.markdown(
                '<div class="empty-box">Belum ada transaksi.</div>',
                unsafe_allow_html=True,
            )
            return

        filtered = dataframe.copy()
        if transaction_filter != "Semua":
            filtered = filtered[
                filtered["Tipe"] == transaction_filter
            ]

        table = filtered[
            ["Tanggal", "Deskripsi", "Kategori", "Tipe", "Jumlah"]
        ].copy()

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Jumlah": st.column_config.NumberColumn(
                    "Jumlah",
                    format="Rp%d",
                )
            },
        )

        st.caption(f"Total {len(filtered)} transaksi")
