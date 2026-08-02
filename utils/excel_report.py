from datetime import date
from io import BytesIO

import pandas as pd


def create_excel_report(
    dataframe: pd.DataFrame,
    total_income: int,
    total_expense: int,
    net_result: int,
    expense_ratio: float,
) -> BytesIO:
    buffer = BytesIO()

    summary = pd.DataFrame(
        {
            "Keterangan": [
                "Total Pemasukan",
                "Total Pengeluaran",
                "Laba/Rugi Bersih",
                "Rasio Pengeluaran",
                "Jumlah Transaksi",
                "Tanggal Laporan",
            ],
            "Nilai": [
                total_income,
                total_expense,
                net_result,
                f"{expense_ratio:.1f}%",
                len(dataframe),
                date.today().isoformat(),
            ],
        }
    )

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Transaksi")
        summary.to_excel(writer, index=False, sheet_name="Ringkasan")

        transaction_sheet = writer.book["Transaksi"]
        summary_sheet = writer.book["Ringkasan"]

        for column, width in {
            "A": 17,
            "B": 34,
            "C": 22,
            "D": 18,
            "E": 18,
            "F": 20,
        }.items():
            transaction_sheet.column_dimensions[column].width = width

        summary_sheet.column_dimensions["A"].width = 25
        summary_sheet.column_dimensions["B"].width = 24

        for cell in transaction_sheet[1]:
            cell.font = cell.font.copy(bold=True)

        for cell in summary_sheet[1]:
            cell.font = cell.font.copy(bold=True)

        for row in range(2, transaction_sheet.max_row + 1):
            transaction_sheet[f"E{row}"].number_format = '"Rp"#,##0'

        for cell_address in ("B2", "B3", "B4"):
            summary_sheet[cell_address].number_format = '"Rp"#,##0'

        transaction_sheet.freeze_panes = "A2"
        summary_sheet.freeze_panes = "A2"

    buffer.seek(0)
    return buffer
