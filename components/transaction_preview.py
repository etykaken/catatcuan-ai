import pandas as pd
import streamlit as st


def render_transaction_preview(transactions: list[dict]) -> tuple[list[dict], bool, bool]:
    with st.container(border=True):
        st.markdown('<div class="card-kicker">✦ &nbsp; INI YANG SAYA PAHAMI</div>', unsafe_allow_html=True)
        if not transactions:
            st.markdown(
                """
                <div class="preview-empty">
                    <div>✧</div><strong>Belum ada transaksi untuk ditinjau</strong>
                    <p>Ceritakan transaksi di sebelah kiri. Hasil yang dipahami AI akan muncul di sini.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return [], False, False

        preview_df = pd.DataFrame(transactions)
        columns = ["Deskripsi", "Kategori", "Tipe", "Jumlah"]
        edited_df = st.data_editor(
            preview_df[columns].copy(), use_container_width=True, hide_index=True,
            num_rows="fixed",
            column_config={
                "Deskripsi": st.column_config.TextColumn("Deskripsi", required=True),
                "Kategori": st.column_config.TextColumn("Kategori", required=True),
                "Tipe": st.column_config.SelectboxColumn("Jenis", options=["Pemasukan", "Pengeluaran"], required=True),
                "Jumlah": st.column_config.NumberColumn("Jumlah", min_value=1, step=1000, format="Rp %d", required=True),
            },
            key="transaction_preview_editor",
        )
        if "Tanggal" in preview_df.columns:
            st.caption(f"Tanggal: {preview_df.iloc[0]['Tanggal']}")
        save_col, cancel_col = st.columns([2, 1])
        with save_col:
            save_button = st.button("✓  Simpan transaksi", type="primary", use_container_width=True, key="save_pending_transactions")
        with cancel_col:
            cancel_button = st.button("Batal", use_container_width=True, key="cancel_pending_transactions")

    edited_transactions = []
    for index, row in edited_df.iterrows():
        original = transactions[index].copy()
        original.update({
            "Deskripsi": str(row["Deskripsi"]).strip(),
            "Kategori": str(row["Kategori"]).strip(),
            "Tipe": str(row["Tipe"]),
            "Jumlah": int(row["Jumlah"]),
        })
        edited_transactions.append(original)
    return edited_transactions, save_button, cancel_button
