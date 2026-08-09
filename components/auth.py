import streamlit as st


def render_auth() -> tuple[str, str, str, bool]:
    st.markdown(
        """
        <div class="auth-shell">
            <div class="auth-brand">
                <div class="auth-kicker">CatatCuan AI</div>

                <h1 class="auth-title">
                    Catat keuangan<br>
                    semudah bercerita.
                </h1>

                <p class="auth-description">
                    Masuk untuk melanjutkan pencatatan transaksi,
                    melihat kondisi usaha, dan mendapatkan insight
                    keuangan dari CatatCuan.
                </p>

                <div class="auth-message">
                    Tell your story. We'll handle the numbers.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_signup = st.tabs(
        ["Masuk", "Buat akun"]
    )

    email = ""
    password = ""
    mode = ""
    submitted = False

    with tab_login:
        st.markdown(
            """
            <div class="auth-form-title">
                Selamat datang kembali
            </div>

            <div class="auth-form-helper">
                Masuk untuk melanjutkan ke CatatCuan.
            </div>
            """,
            unsafe_allow_html=True,
        )

        login_email = st.text_input(
            "Email",
            placeholder="nama@email.com",
            key="login_email",
        )

        login_password = st.text_input(
            "Password",
            type="password",
            placeholder="Masukkan password",
            key="login_password",
        )

        login_button = st.button(
            "Masuk →",
            type="primary",
            use_container_width=True,
            key="login_button",
        )

        if login_button:
            email = login_email
            password = login_password
            mode = "login"
            submitted = True

    with tab_signup:
        st.markdown(
            """
            <div class="auth-form-title">
                Mulai pakai CatatCuan
            </div>

            <div class="auth-form-helper">
                Buat akun untuk menyimpan transaksi usahamu.
            </div>
            """,
            unsafe_allow_html=True,
        )

        signup_email = st.text_input(
            "Email",
            placeholder="nama@email.com",
            key="signup_email",
        )

        signup_password = st.text_input(
            "Password",
            type="password",
            placeholder="Minimal 8 karakter",
            key="signup_password",
        )

        signup_button = st.button(
            "Buat akun →",
            type="primary",
            use_container_width=True,
            key="signup_button",
        )

        if signup_button:
            email = signup_email
            password = signup_password
            mode = "signup"
            submitted = True

    return mode, email, password, submitted
