import pandas as pd
import streamlit as st


def render_transaction_preview(
    transactions: list[dict],
) -> tuple[list[dict], bool, bool]:

    if not transactions:
        with st.container(border=True):
            st.markdown(
                """
                <div class="section-title">
                    <span class="section-number">2</span>
                    Preview transaksi
                </div>
                <div class="section-helper">
                    Hasil transaksi yang dipahami CatatCuan akan muncul di sini.
                </div>
                <div class="preview-empty">
                    <div class="preview-empty-icon">✦</div>
                    <strong>Siap memahami ceritamu</strong>
                    <span>Tulis transaksi di sebelah kiri, lalu pilih Catat transaksi.</span>
                </div>
            """,
                unsafe_allow_html=True,
            )
        return [], False, False

    with st.container(border=True):
        st.markdown(
            """
            <div class="section-title">
                <span class="section-number">2</span>
                CatatCuan memahami ceritamu seperti ini
            </div>

            <div class="section-helper">
                Periksa dan koreksi jika ada yang kurang tepat
                sebelum transaksi disimpan.
            </div>
            """,
            unsafe_allow_html=True,
        )

        preview_df = pd.DataFrame(transactions)

        editable_df = preview_df[
            [
                "Deskripsi",
                "Kategori",
                "Tipe",
                "Jumlah",
            ]
        ].copy()

        edited_df = st.data_editor(
            editable_df,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            column_config={
                "Deskripsi": st.column_config.TextColumn(
                    "Transaksi",
                    width="large",
                    required=True,
                ),
                "Kategori": st.column_config.TextColumn(
                    "Kategori",
                    width="medium",
                    required=True,
                ),
                "Tipe": st.column_config.SelectboxColumn(
                    "Tipe",
                    options=[
                        "Pemasukan",
                        "Pengeluaran",
                    ],
                    required=True,
                    width="small",
                ),
                "Jumlah": st.column_config.NumberColumn(
                    "Nominal",
                    min_value=1,
                    step=1000,
                    format="Rp %d",
                    required=True,
                ),
            },
            key="transaction_preview_editor",
        )

        st.caption(
            f"{len(transactions)} transaksi ditemukan. "
            "Kamu tetap punya kontrol sebelum data disimpan."
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

    edited_transactions = []

    for index, row in edited_df.iterrows():
        original = transactions[index].copy()

        original["Deskripsi"] = str(
            row["Deskripsi"]
        ).strip()

        original["Kategori"] = str(
            row["Kategori"]
        ).strip()

        original["Tipe"] = str(
            row["Tipe"]
        )

        original["Jumlah"] = int(
            row["Jumlah"]
        )

        edited_transactions.append(original)

    return (
        edited_transactions,
        save_button,
        cancel_button,
    )
