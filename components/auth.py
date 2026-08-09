import streamlit as st


def render_auth() -> tuple[str, str, str, bool]:
    st.markdown(
        '<div class="auth-kicker">CATATCUAN AI</div>',
        unsafe_allow_html=True,
    )

    st.title("Catat keuangan semudah bercerita.")

    st.write(
        "Masuk untuk melanjutkan pencatatan usahamu, "
        "melihat ringkasan keuangan, dan mendapatkan "
        "insight yang lebih mudah dipahami."
    )

    st.caption(
        "Ceritakan transaksimu. Biar CatatCuan yang urus angkanya."
    )

    st.write("")

    tab_login, tab_signup = st.tabs(
        ["Masuk", "Buat akun"]
    )

    mode = ""
    email = ""
    password = ""
    submitted = False

    with tab_login:
        st.markdown("### Selamat datang kembali")

        st.caption(
            "Masuk untuk melanjutkan ke CatatCuan."
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
            clean_email = login_email.strip()

            if not clean_email:
                st.warning("Masukkan email terlebih dahulu.")

            elif not login_password:
                st.warning("Masukkan password terlebih dahulu.")

            else:
                mode = "login"
                email = clean_email
                password = login_password
                submitted = True

    with tab_signup:
        st.markdown("### Mulai pakai CatatCuan")

        st.caption(
            "Buat akun untuk menyimpan transaksi "
            "dan melanjutkan pencatatan usahamu."
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

        signup_password_confirm = st.text_input(
            "Konfirmasi password",
            type="password",
            placeholder="Ulangi password",
            key="signup_password_confirm",
        )

        st.caption(
            "Gunakan minimal 8 karakter agar akun lebih aman."
        )

        signup_button = st.button(
            "Buat akun →",
            type="primary",
            use_container_width=True,
            key="signup_button",
        )

        if signup_button:
            clean_email = signup_email.strip()

            if not clean_email:
                st.warning("Masukkan email terlebih dahulu.")

            elif len(signup_password) < 8:
                st.warning(
                    "Password harus terdiri dari minimal 8 karakter."
                )

            elif signup_password != signup_password_confirm:
                st.warning(
                    "Konfirmasi password belum sama."
                )

            else:
                mode = "signup"
                email = clean_email
                password = signup_password
                submitted = True

    return mode, email, password, submitted
