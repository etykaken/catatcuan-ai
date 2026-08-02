import html
import pandas as pd

from utils.formatters import format_rupiah


def build_insights(
    dataframe: pd.DataFrame,
    total_income: int,
    total_expense: int,
    net_result: int,
    expense_ratio: float,
) -> list[str]:
    if dataframe.empty:
        return [
            "Belum ada transaksi. Masukkan transaksi pertama untuk melihat analisis.",
            "Catat transaksi menggunakan bahasa sehari-hari.",
            "CatatCuan AI akan menyusun transaksi menjadi data terstruktur.",
        ]

    insights = []

    if net_result > 0:
        insights.append(
            f"Usaha mencatat laba bersih <strong>{format_rupiah(net_result)}</strong>."
        )
    elif net_result < 0:
        insights.append(
            f"Usaha mencatat kerugian <strong>{format_rupiah(abs(net_result))}</strong>."
        )
    else:
        insights.append("Pemasukan dan pengeluaran sedang berada pada posisi impas.")

    expenses = dataframe[dataframe["Tipe"] == "Pengeluaran"]

    if not expenses.empty:
        totals = (
            expenses.groupby("Kategori")["Jumlah"]
            .sum()
            .sort_values(ascending=False)
        )
        category = str(totals.index[0])
        amount = int(totals.iloc[0])
        share = amount / total_expense * 100 if total_expense else 0

        insights.append(
            f"Pengeluaran terbesar: <strong>{html.escape(category)}</strong> "
            f"({share:.0f}% dari total pengeluaran)."
        )
    else:
        insights.append("Belum ada pengeluaran yang tercatat.")

    if total_income > 0:
        if expense_ratio <= 50:
            condition = "masih sehat"
        elif expense_ratio <= 80:
            condition = "perlu diawasi"
        else:
            condition = "tinggi dan perlu dievaluasi"

        insights.append(
            f"Rasio pengeluaran <strong>{expense_ratio:.0f}%</strong> dan {condition}."
        )
    else:
        insights.append("Belum ada pemasukan untuk menghitung rasio pengeluaran.")

    return insights
