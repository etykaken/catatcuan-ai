import base64
import html
from pathlib import Path

import streamlit as st


def _logo_data_uri(path: Path) -> str:
    if not path.exists():
        return ""

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_header() -> None:
    if "language" not in st.session_state:
        st.session_state.language = "id"

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = False

    if "user" not in st.session_state:
        st.session_state.user = None

    language = st.session_state.language
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
    logo_uri = _logo_data_uri(logo_path)
    logo = f'<img src="{logo_uri}" alt="CatatCuan AI">' if logo_uri else "CC"

    nav_labels = (
        ("Dashboard", "Catat Transaksi", "Arus Kas", "Riwayat")
        if language == "id"
        else ("Dashboard", "Record Transaction", "Cash Flow", "History")
    )

    st.markdown(
        f"""
        <aside class="desktop-sidebar">
            <div class="sidebar-brand">
                <div class="sidebar-logo">{logo}</div>
                <div><strong>CatatCuan</strong><span>AI Finance</span></div>
            </div>
            <nav class="sidebar-nav" aria-label="Dashboard navigation">
                <a class="active" href="#dashboard"><span>⌂</span>{nav_labels[0]}</a>
                <a href="#catat-transaksi"><span>＋</span>{nav_labels[1]}</a>
                <a href="#arus-kas"><span>⌁</span>{nav_labels[2]}</a>
                <a href="#riwayat"><span>▤</span>{nav_labels[3]}</a>
            </nav>
            <div class="sidebar-help">
                <div class="sidebar-help-icon">?</div>
                <strong>{'Butuh bantuan?' if language == 'id' else 'Need help?'}</strong>
                <span>{'Ceritakan transaksi seperti biasa.' if language == 'id' else 'Describe transactions naturally.'}</span>
            </div>
            <div class="sidebar-version">CatatCuan AI · v1.0</div>
        </aside>
        <div id="dashboard"></div>
        """,
        unsafe_allow_html=True,
    )

    title_col, language_col, account_col = st.columns(
        [5.2, 1.15, 1.75], gap="small", vertical_alignment="center"
    )

    with title_col:
        eyebrow = "DASHBOARD KEUANGAN" if language == "id" else "FINANCIAL DASHBOARD"
        greeting = "Selamat datang kembali 👋" if language == "id" else "Welcome back 👋"
        st.markdown(
            f'<div class="dashboard-heading"><span>{eyebrow}</span><strong>{greeting}</strong></div>',
            unsafe_allow_html=True,
        )

    with language_col:
        language_choice = st.radio(
            "Language",
            options=["ID", "EN"],
            index=0 if language == "id" else 1,
            horizontal=True,
            label_visibility="collapsed",
            key="header_language",
        )
        new_language = "id" if language_choice == "ID" else "en"
        if new_language != language:
            st.session_state.language = new_language
            st.rerun()

    with account_col:
        if st.session_state.user is None:
            auth_label = "Masuk / Daftar" if language == "id" else "Sign in / Register"
            if st.button(auth_label, use_container_width=True, key="header_auth_button"):
                st.session_state.auth_mode = True
                st.rerun()
        else:
            user_email = getattr(st.session_state.user, "email", "")
            st.markdown(
                f'<div class="account-chip"><span>●</span>{html.escape(user_email or "Account")}</div>',
                unsafe_allow_html=True,
            )

    hero_title = (
        "Catat keuangan, <span>lebih mudah.</span>"
        if language == "id"
        else "Track finances, <span>made simple.</span>"
    )
    hero_copy = (
        "Ceritakan aktivitas usahamu dengan bahasa sehari-hari. CatatCuan akan merapikan transaksi dan menampilkan kondisi keuanganmu."
        if language == "id"
        else "Describe your business activity naturally. CatatCuan organizes each transaction and shows your financial position."
    )
    st.markdown(
        f"""
        <section class="dashboard-hero">
            <div><h1>{hero_title}</h1><p>{hero_copy}</p></div>
            <div class="hero-badge"><span>✦</span><strong>AI Powered</strong><small>Financial assistant</small></div>
        </section>
        <div id="catat-transaksi"></div>
        """,
        unsafe_allow_html=True,
    )
