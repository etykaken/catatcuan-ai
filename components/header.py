import base64
import html
from datetime import datetime
from pathlib import Path

import streamlit as st


def _logo_data_uri() -> str:
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
    if not logo_path.exists():
        return ""
    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_header() -> None:
    """Render the fixed desktop navigation and compact dashboard header."""
    user = st.session_state.get("user")
    email = getattr(user, "email", "") if user else ""
    display_name = email.split("@")[0].replace(".", " ").title() if email else "Budi Santoso"
    first_name = display_name.split()[0] if display_name else "Budi"
    initials = "".join(part[0] for part in display_name.split()[:2]).upper() or "BS"
    logo_uri = _logo_data_uri()
    month_label = datetime.now().strftime("%B %Y")
    month_names = {
        "January": "Januari", "February": "Februari", "March": "Maret",
        "April": "April", "May": "Mei", "June": "Juni", "July": "Juli",
        "August": "Agustus", "September": "September", "October": "Oktober",
        "November": "November", "December": "Desember",
    }
    english_month, year = month_label.split()
    period = f"{month_names[english_month]} {year}"
    logo = f'<img src="{logo_uri}" alt="CatatCuan AI">' if logo_uri else "✦ CatatCuan AI"

    st.markdown(
        f"""
        <aside class="cc-sidebar">
            <div class="sidebar-brand">{logo}</div>
            <p class="sidebar-tagline">Catat keuangan<br>semudah bercerita.</p>
            <nav class="sidebar-nav" aria-label="Navigasi utama">
                <div class="nav-item active"><span>⌂</span>Beranda</div>
                <div class="nav-item"><span>⇄</span>Transaksi</div>
                <div class="nav-item"><span>✧</span>Insight AI</div>
                <div class="nav-item"><span>▤</span>Laporan</div>
                <div class="nav-divider"></div>
                <div class="nav-item"><span>♙</span>Akun</div>
                <div class="nav-item"><span>⌁</span>Integrasi</div>
                <div class="nav-item"><span>⚙</span>Pengaturan</div>
            </nav>
            <div class="sidebar-bottom">
                <div class="promo-card">
                    <div class="promo-mascot">✦</div>
                    <strong>CatatCuan AI</strong>
                    <p>Asisten keuangan pintar yang siap membantumu 24/7.</p>
                    <span>Pelajari lebih lanjut →</span>
                </div>
                <div class="user-card">
                    <div class="user-avatar">{html.escape(initials)}</div>
                    <div><strong>{html.escape(display_name)}</strong><small>{html.escape(email or 'Warung Pak Budi')}</small></div>
                    <span>⌄</span>
                </div>
            </div>
        </aside>
        <header class="dashboard-header">
            <div>
                <h1>Selamat pagi, {html.escape(first_name)}! 👋</h1>
                <p>Yuk catat transaksi hari ini, biar keuangan usahamu makin sehat.</p>
            </div>
            <div class="header-actions">
                <div class="period-pill">▣&nbsp;&nbsp; {period}&nbsp;⌄</div>
                <div class="icon-button" aria-label="Notifikasi">♧</div>
                <div class="header-avatar">{html.escape(initials)}</div>
            </div>
        </header>
        """,
        unsafe_allow_html=True,
    )

    # Keep the existing authentication entry point without turning navigation
    # into Streamlit radio controls.
    if user is None:
        if st.button("Masuk", key="header_auth_button"):
            st.session_state.auth_mode = True
            st.rerun()
