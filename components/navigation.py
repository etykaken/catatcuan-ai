import streamlit as st


NAVIGATION_ITEMS = (
    "Dashboard",
    "Catat Transaksi",
    "Laporan Keuangan",
    "Assessment",
    "AI Assistant",
    "Account",
)


def render_navigation() -> str:
    """Render the primary app navigation and return the active view."""
    if "active_view" not in st.session_state:
        st.session_state.active_view = NAVIGATION_ITEMS[0]

    if st.session_state.active_view not in NAVIGATION_ITEMS:
        st.session_state.active_view = NAVIGATION_ITEMS[0]

    return st.radio(
        "Navigasi utama",
        options=NAVIGATION_ITEMS,
        horizontal=True,
        label_visibility="collapsed",
        key="active_view",
    )
