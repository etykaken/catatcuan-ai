from datetime import date, timedelta
from io import BytesIO

import pandas as pd
import streamlit as st

from services.gemini_service import analyze_transactions


MAX_INPUT_LENGTH = 1000
MAX_AMOUNT = 10_000_000_000


def resolve_date(value: str) -> str:
    """Mengubah tanggal relatif dari AI menjadi tanggal aktual."""
    today = date.today()
    normalized_value = str(value).strip().upper()

    if normalized_value == "TODAY":
        return today.isoformat()

    if normalized_value == "YESTERDAY":
        return (today - timedelta(days=1)).isoformat()

    return str(value)


def format_rupiah(value: int) -> str:
    """Mengubah angka menjadi format Rupiah."""
    return f"Rp{value:,.0f}".replace(",", ".")


def validate_transactions(raw_transactions: list) -> list:
    """Memeriksa hasil AI sebelum ditampilkan."""
    validated_transactions = []

    for item in raw_transactions:
        transaction_type = item.get("type")
        amount = item.get("amount")

        if transaction_type not in {"income", "expense"}:
            continue

        if not isinstance(amount, int):
            continue

        if amount <= 0 or amount > MAX_AMOUNT:
            continue

        validated_transactions.append(
            {
                "Tanggal": resolve_date(
                    item.get("date", "TODAY")
                ),
                "Jenis": (
                    "Pemasukan"
                    if transaction_type == "income"
                    else "Pengeluaran"
                ),
                "Kategori": str(
                    item.get("category", "")
                ).strip(),
                "Keterangan": str(
                    item.get("description", "")
                ).strip()[:120],
                "Nominal": amount,
                "Perlu Konfirmasi": (
                    "Ya"
                    if item.get("requires_confirmation", False)
                    else "Tidak"
                ),
            }
        )

    return validated_transactions


st.set_page_config(
    page_title="CatatCuan AI",
    page_icon="assets/favicon.png",
    layout="wide",
)

st.image(
    "assets/logo.png",
    width=380,
)

st.caption("Catat keuangan semudah bercerita.")

st.info(
    "Contoh: Hari ini jual kopi Rp300.000, "
    "beli susu Rp80.000, dan bayar parkir Rp5.000."
)

user_input = st.text_area(
    "Ceritakan transaksi usaha kamu",
    placeholder=(
        "Tulis pemasukan dan pengeluaran "
        "menggunakan bahasa sehari-hari..."
    ),
    height=150,
    max_chars=MAX_INPUT_LENGTH,
)

analyze_button = st.button(
    "Analisis Transaksi",
    type="primary",
    use_container_width=True,
)

if analyze_button:
    if not user_input.strip():
        st.warning("Tulis transaksi terlebih dahulu.")
        st.stop()

    try:
        api_key = st.secrets["GEMINI_API_KEY"]

    except (FileNotFoundError, KeyError):
        st.error(
            "GEMINI_API_KEY belum dipasang "
            "di Streamlit Secrets."
        )
        st.stop()

    try:
        with st.spinner(
            "CatatCuan AI sedang membaca transaksi..."
        ):
            result = analyze_transactions(
                api_key=api_key,
                user_input=user_input.strip(),
            )

        transactions = validate_transactions(
            result.get("transactions", [])
        )

        if not transactions:
            st.warning(
                "Tidak ditemukan transaksi yang dapat dicatat."
            )
            st.stop()

        dataframe = pd.DataFrame(transactions)

        total_income = int(
            dataframe.loc[
                dataframe["Jenis"] == "Pemasukan",
                "Nominal",
            ].sum()
        )

        total_expense = int(
            dataframe.loc[
                dataframe["Jenis"] == "Pengeluaran",
                "Nominal",
            ].sum()
        )

        balance = total_income - total_expense
        if total_income > 0:
            expense_ratio = (
                total_expense / total_income
            ) * 100
        else:
            expense_ratio = 0
        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Pemasukan",
            format_rupiah(total_income),
        )

        col2.metric(
            "Total Pengeluaran",
            format_rupiah(total_expense),
        )

        col3.metric(
            "Selisih",
            format_rupiah(balance),
        )
        st.subheader("💡 Insight Keuangan")

        if balance > 0:
            st.success(
                f"Arus kas positif sebesar "
                f"{format_rupiah(balance)}."
            )
        elif balance < 0:
            st.warning(
                f"Pengeluaran melebihi pemasukan sebesar "
                f"{format_rupiah(abs(balance))}."
            )
        else:
            st.info(
                "Pemasukan dan pengeluaran berada "
                "pada jumlah yang sama."
            )

        if total_income > 0:
            st.write(
                f"Pengeluaran menggunakan "
                f"{expense_ratio:.1f}% dari total pemasukan."
            )
        elif total_expense > 0:
            st.write(
                "Belum ada pemasukan yang tercatat, "
                "tetapi sudah terdapat pengeluaran."
            )
        st.subheader("Hasil Pencatatan")

        display_dataframe = dataframe.copy()
        display_dataframe["Nominal"] = (
            display_dataframe["Nominal"].apply(
                format_rupiah
            )
        )

        st.dataframe(
            display_dataframe,
            use_container_width=True,
            hide_index=True,
        )

        excel_buffer = BytesIO()

        with pd.ExcelWriter(
            excel_buffer,
            engine="openpyxl",
        ) as writer:
            dataframe.to_excel(
                writer,
                index=False,
                sheet_name="Laporan",
            )

        excel_buffer.seek(0)

        st.download_button(
            label="📥 Download Laporan Excel",
            data=excel_buffer,
            file_name=(
                f"CatatCuanAI_"
                f"{date.today().isoformat()}.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

        confirmation_count = int(
            dataframe["Perlu Konfirmasi"] == "Ya").sum()
        )
        if confirmation_count > 0:
            st.warning(
                f"{confirmation_count} transaksi perlu "
                "diperiksa kembali."
            )
        else:
            st.success(
                "Semua transaksi berhasil dibaca."
            )

    except Exception:
        st.error(
            "Transaksi gagal diproses. "
            "Silakan coba kembali."
        )

st.divider()

st.caption(
    "CatatCuan AI adalah MVP. Periksa kembali hasil "
    "pencatatan sebelum mengambil keputusan keuangan."
)
