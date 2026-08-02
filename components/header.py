import streamlit as st


def render_header() -> None:
    st.markdown(
        """
        <div class="topbar">
            <div class="brand-wrap">
                <div class="brand-logo">🤖</div>
                <div>
                    <div class="brand-name">CatatCuan AI</div>
                    <div class="brand-subtitle">AI Financial Assistant</div>
                </div>
            </div>
            <div class="profile-pill">
                <div class="profile-avatar">👩🏻</div>
                <div class="profile-name">Etyka K.</div>
            </div>
        </div>

        <section class="hero">
            <div class="hero-copy">
                <div class="hero-title">
                    Catat pemasukan &amp; pengeluaran<br>
                    semudah <span>bercerita.</span>
                </div>
                <div class="hero-description">
                    AI membantu membaca transaksi, membuat pencatatan otomatis,
                    serta memberikan insight keuangan usaha.
                </div>
            </div>
            <div class="hero-emoji">🤖</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
