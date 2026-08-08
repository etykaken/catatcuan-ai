import pandas as pd
import streamlit as st


def render_transaction_preview(
    transactions: list[dict],
) -> tuple[bool, bool]:
    if not transactions:
        return False, False

    with st.container(border=True):
        st.markdown(
            """
            <div class="section-title">
                CatatCuan memahami ceritamu seperti ini
            </div>

            <div class="section-helper">
                Periksa dulu sebelum transaksi disimpan.
            </div>
            """,
            unsafe_allow_html=True,
        )

        preview_df = pd.DataFrame(transactions)

        visible_columns = [
            "Deskripsi",
            "Kategori",
            "Tipe",
            "Jumlah",
        ]

        preview_df = preview_df[
            [
                column
                for column in visible_columns
                if column in preview_df.columns
            ]
        ]

        st.dataframe(
            preview_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Deskripsi": st.column_config.TextColumn(
                    "Transaksi",
                    width="large",
                ),
                "Kategori": st.column_config.TextColumn(
                    "Kategori",
                    width="medium",
                ),
                "Tipe": st.column_config.TextColumn(
                    "Tipe",
                    width="small",
                ),
                "Jumlah": st.column_config.NumberColumn(
                    "Nominal",
                    format="Rp %d",
                ),
            },
        )

        st.caption(
            f"{len(transactions)} transaksi ditemukan oleh CatatCuan."
        )

        cancel_column, save_column = st.columns(
            [1, 2],
            gap="small",
        )

        with cancel_column:
            cancel_button = st.button(
                "Batal",
                use_container_width=True,
                key="cancel_pending_transactions",
            )

        with save_column:
            save_button = st.button(
                f"Simpan {len(transactions)} transaksi →",
                type="primary",
                use_container_width=True,
                key="save_pending_transactions",
            )

    return save_button, cancel_button
