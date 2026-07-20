import streamlit as st

st.set_page_config(
    page_title="CatatCuan AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = {
    "MENU UTAMA": [
        st.Page(
            "dashboard.py",
            title="Dashboard",
            icon="🏠",
            default=True,
        ),
        st.Page(
            "pages/transaksi.py",
            title="Transaksi",
            icon="🧾",
        ),
        st.Page(
            "pages/ai_insight.py",
            title="AI Insight",
            icon="✨",
        ),
        st.Page(
            "pages/ai_chat.py",
            title="AI Chat",
            icon="🤖",
        ),
        st.Page(
            "pages/laporan.py",
            title="Laporan",
            icon="📊",
        ),
    ],
    "LAINNYA": [
        st.Page(
            "pages/pengaturan.py",
            title="Pengaturan",
            icon="⚙️",
        ),
    ],
}

navigation = st.navigation(pages)
navigation.run()
