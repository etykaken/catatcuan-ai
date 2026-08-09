import streamlit as st


def render_header() -> None:
    if "language" not in st.session_state:
        st.session_state.language = "id"

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = False

    top_left, top_right = st.columns(
        [4.8, 2.2],
        vertical_alignment="center",
    )

    # =========================
    # BRAND
    # =========================
    with top_left:
        st.markdown(
            """
<div class="topbar-brand">
    <div class="brand-logo">🤖</div>

    <div>
        <div class="brand-name">
            CatatCuan AI
        </div>

        <div class="brand-subtitle">
            AI Financial Assistant
        </div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    # =========================
    # ACTIONS
    # =========================
    with top_right:
        lang_col, auth_col = st.columns(
            [0.7, 1.5],
            gap="small",
        )

        with lang_col:
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

            selected_language = (
                "id"
                if language_choice == "ID"
                else "en"
            )

            if (
                selected_language
                != st.session_state.language
            ):
                st.session_state.language = (
                    selected_language
                )
                st.rerun()

        with auth_col:
            if st.session_state.get("user") is None:
                if st.button(
                    "Masuk / Buat akun"
                    if st.session_state.language == "id"
                    else "Sign in / Create account",
                    use_container_width=True,
                    key="header_auth_button",
                ):
                    st.session_state.auth_mode = True
                    st.rerun()

            else:
                user = st.session_state.user
                user_email = getattr(
                    user,
                    "email",
                    "",
                )

                st.caption(
                    user_email
                    if user_email
                    else "Account"
                )

    # =========================
    # HERO
    # =========================

    if st.session_state.language == "id":
        hero_title = (
            "Catat pemasukan &amp; pengeluaran<br>"
            "semudah <span>bercerita.</span>"
        )

        hero_description = (
            "Ceritakan transaksi usahamu dengan bahasa sehari-hari. "
            "CatatCuan membantu merapikan pencatatan dan memberikan "
            "insight keuangan yang lebih mudah dipahami."
        )

    else:
        hero_title = (
            "Track income &amp; expenses<br>"
            "as naturally as <span>telling a story.</span>"
        )

        hero_description = (
            "Describe your daily business transactions naturally. "
            "CatatCuan helps organize your records and turn them "
            "into clearer financial insights."
        )

    st.markdown(
        f"""
<section class="hero">
    <div class="hero-copy">

        <div class="hero-title">
            {hero_title}
        </div>

        <div class="hero-description">
            {hero_description}
        </div>

    </div>

    <div class="hero-emoji">
        🤖
    </div>
</section>
""",
        unsafe_allow_html=True,
    )
