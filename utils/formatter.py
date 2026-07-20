"""Fungsi format tampilan (angka -> string yang enak dibaca)."""


def format_rupiah(value: int | float) -> str:
    """Ubah angka menjadi format Rupiah, contoh: 1500000 -> 'Rp1.500.000'."""
    return f"Rp{value:,.0f}".replace(",", ".")
