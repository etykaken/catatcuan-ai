import base64
from pathlib import Path

import streamlit as st


def render_header() -> None:
    if "language" not in st.session_state:
        st.session_state.language = "id"

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = False

    if "user" not in st.session_state:
        st.session_state.user = None

    # =====================================================
    # TOP HEADER
    # =====================================================

    brand_col, language_col, account_col = st.columns(
        [4.5, 1.2, 1.8],
        gap="small",
        vertical_alignment="center",
    )

    # =====================================================
    # BRAND
    # =====================================================

    with brand_col:
        logo_path = (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "logo.png"
        )

        logo_col, name_col = st.columns(
            [0.6, 4.4],
            gap="small",
            vertical_alignment="center",
        )

        with logo_col:
            if logo_path.exists():
                st.image(
                    str(logo_path),
                    width=46,
                )
            else:
                st.markdown("### 🤖")

        with name_col:
            st.markdown("### CatatCuan AI")
            st.caption("AI Financial Assistant")

    # =====================================================
    # LANGUAGE
    # =====================================================

    with language_col:
        language_choice = st.radio(
            "Language",
            options=["ID", "EN"],
            index=(
                0
                if st.session_state.language == "id"
                else 1
            ),
            horizontal=True,
            label_visibility="collapsed",
            key="header_language",
        )

        new_language = (
            "id"
            if language_choice == "ID"
            else "en"
        )

        if new_language != st.session_state.language:
            st.session_state.language = new_language
            st.rerun()

    # =====================================================
    # ACCOUNT
    # =====================================================

    with account_col:
        if st.session_state.user is None:
            auth_label = (
                "Masuk / Buat akun"
                if st.session_state.language == "id"
                else "Sign in / Create account"
            )

            if st.button(
                auth_label,
                use_container_width=True,
                key="header_auth_button",
            ):
                st.session_state.auth_mode = True
                st.rerun()

        else:
            user_email = getattr(
                st.session_state.user,
                "email",
                "",
            )

            st.caption(
                user_email
                if user_email
                else "Account"
            )

    st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)

    # =====================================================
    # HERO
    # =====================================================

    if st.session_state.language == "id":
        kicker = "Dashboard keuangan"
        title = "Selamat datang di CatatCuan 👋"
        description = (
            "Pantau arus kas, catat transaksi, dan pahami kondisi "
            "usaha dalam satu dashboard sederhana."
        )
    else:
        kicker = "Financial dashboard"
        title = "Welcome to CatatCuan 👋"
        description = (
            "Track cash flow, record transactions, and understand "
            "your business in one simple dashboard."
        )

    if logo_path.exists():
        logo_data = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        hero_visual = (
            f'<img src="data:image/png;base64,{logo_data}" '
            'alt="CatatCuan" class="hero-logo">'
        )
    else:
        hero_visual = '<div class="hero-emoji">🤖</div>'

    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-copy">
                <div class="hero-kicker">{kicker}</div>
                <div class="hero-title">{title}</div>
                <div class="hero-description">{description}</div>
            </div>
            <div class="hero-visual">{hero_visual}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
