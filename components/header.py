import html
from datetime import datetime
import streamlit as st


def _user_details() -> tuple[str, str, str]:
    user = st.session_state.get("user")
    email = getattr(user, "email", "") if user else ""
    metadata = getattr(user, "user_metadata", {}) or {} if user else {}
    name = metadata.get("full_name") or metadata.get("name") or ""
    if not name and email:
        name = email.split("@", 1)[0].replace(".", " ").title()
    display_name = name or ("Pengguna" if st.session_state.language == "id" else "User")
    subtitle = email or ("Mode tamu" if st.session_state.language == "id" else "Guest mode")
    initials = "".join(part[0] for part in display_name.split()[:2]).upper() or "CC"
    return display_name, subtitle, initials


def render_sidebar() -> None:
    language = st.session_state.get("language", "id")
    display_name, subtitle, initials = _user_details()
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand" aria-label="CatatCuan AI">'
            '<span class="brand-spark" aria-hidden="true">✦</span>'
            '<span>CatatCuan</span><b>AI</b></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="sidebar-tagline">Catat keuangan<br>semudah bercerita.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <nav class="app-nav" aria-label="Navigasi utama">
              <div class="nav-item active"><span>⌂</span> Beranda</div>
              <div class="nav-item"><span>☷</span> Transaksi</div>
              <div class="nav-item"><span>✧</span> Insight AI</div>
              <div class="nav-item"><span>▤</span> Laporan</div>
              <div class="nav-divider"></div>
              <div class="nav-item"><span>♙</span> Akun</div>
              <div class="nav-item"><span>⌁</span> Integrasi</div>
              <div class="nav-item"><span>⚙</span> Pengaturan</div>
            </nav>
            <div class="sidebar-spacer"></div>
            <div class="sidebar-ai-card">
              <div class="ai-orb">✦</div><strong>CatatCuan AI</strong>
              <p>Asisten keuangan pintar yang siap membantumu 24/7.</p>
              <span>Pelajari lebih lanjut →</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="user-card"><div class="user-avatar">{html.escape(initials)}</div>'
            f'<div><strong>{html.escape(display_name)}</strong><small>{html.escape(subtitle)}</small></div></div>',
            unsafe_allow_html=True,
        )
        if st.session_state.get("user") is None:
            label = "Masuk / Buat akun" if language == "id" else "Sign in / Create account"
            if st.button(label, key="sidebar_auth_button", use_container_width=True):
                st.session_state.auth_mode = True
                st.rerun()
        language_choice = st.selectbox(
            "Bahasa / Language",
            ["ID", "EN"],
            index=0 if language == "id" else 1,
            key="sidebar_language",
        )
        new_language = "id" if language_choice == "ID" else "en"
        if new_language != language:
            st.session_state.language = new_language
            st.rerun()


def render_header() -> None:
    language = st.session_state.get("language", "id")
    display_name, _, initials = _user_details()
    first_name = display_name.split()[0]
    now = datetime.now()
    month_names = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    if language == "id":
        greeting = f"Selamat pagi, {first_name}! 👋"
        helper = "Yuk catat transaksi hari ini, biar keuangan usahamu makin sehat."
        period = f"{month_names[now.month - 1]} {now.year}"
    else:
        greeting = f"Good morning, {first_name}! 👋"
        helper = "Record today's transactions and keep your business finances healthy."
        period = now.strftime("%B %Y")

    st.markdown(
        f"""
        <header class="dashboard-header">
          <div><h1>{html.escape(greeting)}</h1><p>{html.escape(helper)}</p></div>
          <div class="header-actions"><div class="period-pill"><span aria-hidden="true">▣</span>&nbsp; {html.escape(period)} <span aria-hidden="true">⌄</span></div>
          <div class="icon-pill" aria-label="Notifikasi"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></svg></div><div class="header-avatar">{html.escape(initials)}</div></div>
        </header>
        """,
        unsafe_allow_html=True,
    )
