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

    st.write("")

    # =====================================================
    # HERO
    # =====================================================

    hero_text_col, hero_icon_col = st.columns(
        [5, 1],
        gap="large",
        vertical_alignment="center",
    )

    with hero_text_col:
        if st.session_state.language == "id":
            st.title(
                "Catat pemasukan & pengeluaran "
                "semudah bercerita."
            )

            st.write(
                "Ceritakan transaksi usahamu dengan bahasa "
                "sehari-hari. CatatCuan membantu merapikan "
                "pencatatan dan memberikan insight keuangan "
                "yang lebih mudah dipahami."
            )

        else:
            st.title(
                "Track income & expenses "
                "as naturally as telling a story."
            )

            st.write(
                "Describe your daily business transactions "
                "naturally. CatatCuan helps organize your "
                "records and turn them into clearer "
                "financial insights."
            )

    with hero_icon_col:
        if logo_path.exists():
            st.image(
                str(logo_path),
                width=100,
            )
        else:
            st.markdown("# 🤖")

    st.write("")
