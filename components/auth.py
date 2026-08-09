import streamlit as st


def render_auth() -> tuple[str, str, str, bool]:
    left_column, right_column = st.columns(
        [1.05, 0.95],
        gap="large",
    )

    mode = ""
    email = ""
    password = ""
    submitted = False

    # =========================
    # LEFT — BRAND / VALUE
    # =========================
    with left_column:
        st.markdown(
            """
<div class="auth-copy">
    <div class="auth-eyebrow">CATATCUAN AI</div>

    <h1 class="auth-headline">
        Catat keuangan<br>
        semudah bercerita.
    </h1>

    <div class="auth-subcopy">
        Nggak perlu paham istilah akuntansi.
        Ceritakan transaksi usahamu seperti biasa,
        CatatCuan bantu mengubahnya menjadi catatan
        keuangan yang lebih rapi dan mudah dipahami.
    </div>

    <div class="auth-points">
        <div class="auth-point">
            <span class="auth-point-dot">✓</span>
            Catat transaksi dengan bahasa sehari-hari
        </div>

        <div class="auth-point">
            <span class="auth-point-dot">✓</span>
            Lihat ringkasan pemasukan dan pengeluaran
        </div>

        <div class="auth-point">
            <span class="auth-point-dot">✓</span>
            Dapatkan insight keuangan yang lebih mudah dipahami
        </div>
    </div>

    <div class="auth-tagline">
        Ceritakan transaksimu. Biar CatatCuan yang urus angkanya.
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    # =========================
    # RIGHT — AUTH FORM
    # =========================
    with right_column:
        with st.container(border=True):
            tab_login, tab_signup = st.tabs(
                ["Masuk", "Buat akun"]
            )

            # =========================
            # LOGIN
            # =========================
            with tab_login:
                st.markdown(
                    "## Selamat datang kembali"
                )

                st.caption(
                    "Masuk untuk melanjutkan pencatatan usahamu."
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
                        st.warning(
                            "Masukkan email terlebih dahulu."
                        )

                    elif not login_password:
                        st.warning(
                            "Masukkan password terlebih dahulu."
                        )

                    else:
                        mode = "login"
                        email = clean_email
                        password = login_password
                        submitted = True

            # =========================
            # SIGN UP
            # =========================
            with tab_signup:
                st.markdown(
                    "## Mulai pakai CatatCuan"
                )

                st.caption(
                    "Buat akun untuk menyimpan dan "
                    "melanjutkan pencatatan usahamu."
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
                    "Gunakan minimal 8 karakter."
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
                        st.warning(
                            "Masukkan email terlebih dahulu."
                        )

                    elif len(signup_password) < 8:
                        st.warning(
                            "Password minimal 8 karakter."
                        )

                    elif (
                        signup_password
                        != signup_password_confirm
                    ):
                        st.warning(
                            "Konfirmasi password belum sama."
                        )

                    else:
                        mode = "signup"
                        email = clean_email
                        password = signup_password
                        submitted = True

    return mode, email, password, submitted
