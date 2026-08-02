def format_rupiah(value: int | float) -> str:
    return f"Rp{value:,.0f}".replace(",", ".")
