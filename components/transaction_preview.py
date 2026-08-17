import html
import pandas as pd
import streamlit as st
from utils.formatters import format_rupiah


def render_transaction_preview(transactions: list[dict]) -> tuple[list[dict], bool, bool]:
    language = st.session_state.get("language", "id")
    with st.container(border=True, key="transaction_preview_card"):
        if transactions:
            st.markdown('<div class="mobile-pending-marker"><a href="?view=home" aria-label="Kembali">←</a><strong>Ini yang saya pahami</strong><span>✧</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="card-eyebrow">✦ &nbsp; INI YANG SAYA PAHAMI</div>' if language == "id" else '<div class="card-eyebrow">✦ &nbsp; HERE IS WHAT I UNDERSTOOD</div>', unsafe_allow_html=True)
        if not transactions:
            st.markdown('<div class="preview-empty"><div>✧</div><strong>Belum ada transaksi untuk ditinjau</strong><span>Ceritakan transaksi di sebelah kiri, lalu hasilnya akan muncul di sini.</span></div>' if language == "id" else '<div class="preview-empty"><div>✧</div><strong>No transaction to review</strong><span>Describe a transaction on the left and its details will appear here.</span></div>', unsafe_allow_html=True)
            return [], False, False

        preview_df = pd.DataFrame(transactions)
        editable_df = preview_df[["Deskripsi", "Kategori", "Tipe", "Jumlah"]].copy()
        first = transactions[0]
        date_value = first.get("Tanggal", "—")
        amount_class = "negative" if first.get("Tipe") == "Pengeluaran" else "positive"
        st.markdown(
            '<div class="preview-list">'
            f'<div><span>↕ &nbsp; Jenis</span><strong class="{amount_class}">{html.escape(str(first.get("Tipe", "—")))}</strong></div>'
            f'<div><span>◇ &nbsp; Kategori</span><strong>{html.escape(str(first.get("Kategori", "—")))}</strong></div>'
            f'<div><span>□ &nbsp; Tanggal</span><strong>{html.escape(str(date_value))}</strong></div>'
            f'<div><span>▤ &nbsp; Deskripsi</span><strong>{html.escape(str(first.get("Deskripsi", "—")))}</strong></div>'
            f'<div><span>♧ &nbsp; Jumlah</span><strong class="{amount_class}">{html.escape(format_rupiah(first.get("Jumlah", 0)))}</strong></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="mobile-confirm-note">♢ <span>Pastikan semua sudah sesuai ya.<br>Kamu bisa edit sebelum disimpan.</span></div>', unsafe_allow_html=True)
        with st.expander("Edit detail" if language == "id" else "Edit details"):
            edited_df = st.data_editor(editable_df, use_container_width=True, hide_index=True, num_rows="fixed", column_config={"Tipe": st.column_config.SelectboxColumn("Tipe", options=["Pemasukan", "Pengeluaran"], required=True), "Jumlah": st.column_config.NumberColumn("Jumlah", min_value=1, step=1000, format="Rp %d", required=True)}, key="transaction_preview_editor")
        save_col, cancel_col = st.columns([1.5, 1], gap="small")
        with save_col: save_button = st.button("✓  Simpan transaksi", type="primary", use_container_width=True, key="save_pending_transactions")
        with cancel_col: cancel_button = st.button("Batal" if language == "id" else "Cancel", use_container_width=True, key="cancel_pending_transactions")

    edited_transactions = []
    for index, row in edited_df.iterrows():
        original = transactions[index].copy()
        original.update({"Deskripsi": str(row["Deskripsi"]).strip(), "Kategori": str(row["Kategori"]).strip(), "Tipe": str(row["Tipe"]), "Jumlah": int(row["Jumlah"])})
        edited_transactions.append(original)
    return edited_transactions, save_button, cancel_button
