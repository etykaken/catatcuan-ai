"""
app.py — Entry point CatatCuan AI.

Bertanggung jawab untuk:
1. Konfigurasi halaman & CSS global (dipakai di semua halaman karena
   script ini selalu dijalankan ulang sebelum pg.run()).
2. Inisialisasi session_state (sekali, dan konsisten di semua halaman).
3. Sidebar branding (logo, kartu upgrade, versi).
4. Navigasi multi-halaman lewat st.navigation + st.Page.
"""
from pathlib import Path

import streamlit as st

import dashboard
from pages import ai_chat, ai_insight, laporan, pengaturan, transaksi

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
FAVICON_PATH = ASSETS_DIR / "favicon.png"

try:
    DEBUG_MODE = bool(st.secrets.get("DEBUG_MODE", False))
except (FileNotFoundError, KeyError):
    DEBUG_MODE = False

# ── Konfigurasi Halaman ──────────────────────────────────────────────
st.set_page_config(
    page_title="CatatCuan AI",
    page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else "💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown('''
<style>
:root{--green:#168a4d;--dark:#173d2c;--ink:#18231d;--muted:#6b776f;--line:#e2ebe5;--soft:#eaf7ef}
html,body,[class*="css"]{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}.stApp{background:#f7faf8}.block-container{max-width:1320px;padding-top:1.5rem;padding-bottom:4rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#f4fbf6,#edf7f0);border-right:1px solid var(--line)}[data-testid="stSidebar"] .block-container{padding:1.4rem 1rem}
.brand{display:flex;align-items:center;gap:10px;padding:5px 5px 20px}.brand-mark{width:43px;height:43px;border-radius:13px;display:grid;place-items:center;background:linear-gradient(135deg,#20a65e,#11723f);font-size:22px;box-shadow:0 8px 20px #168a4d38}.brand-title{font-size:18px;font-weight:900;color:var(--ink)}.brand-sub{font-size:11px;color:var(--muted)}
.side-label{font-size:10px;letter-spacing:.12em;color:#91a096;font-weight:800;padding:13px 10px 6px}.upgrade{margin-top:14px;padding:16px;border-radius:16px;background:linear-gradient(145deg,#174c32,#0f3825);color:white}.upgrade b{font-size:14px}.upgrade p{font-size:11px;line-height:1.5;color:#cbe3d3}.version{margin-top:20px;color:#8b9890;font-size:11px}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}.kicker{font-size:13px;color:var(--muted)}.page-title{font-size:28px;font-weight:900;color:var(--ink);letter-spacing:-.03em}.profile{display:flex;align-items:center;gap:9px;padding:7px 11px 7px 8px;border:1px solid var(--line);border-radius:999px;background:white}.avatar{width:32px;height:32px;border-radius:50%;display:grid;place-items:center;background:#dff2e6}.profile-name{font-size:12px;font-weight:800}
.hero{display:flex;justify-content:space-between;align-items:center;min-height:230px;padding:34px 38px;margin-bottom:24px;border:1px solid #dceae1;border-radius:24px;background:radial-gradient(circle at 88% 20%,#4bbe7833,transparent 28%),linear-gradient(135deg,#fff,#effaf3);box-shadow:0 16px 40px #1e52330f;overflow:hidden}.hero-copy{max-width:720px}.eyebrow{font-size:13px;font-weight:850;letter-spacing:.08em;color:var(--green);text-transform:uppercase;margin-bottom:10px}.hero-title{font-size:40px;line-height:1.08;font-weight:950;color:var(--ink);letter-spacing:-.045em}.hero-title span{display:block;color:var(--green)}.hero-sub{font-size:15px;line-height:1.65;color:var(--muted);margin-top:14px;max-width:650px}.hero-art{position:relative;width:300px;height:180px;min-width:300px}.panel{position:absolute;inset:13px 16px 15px;background:#ffffffd9;border:1px solid #d2e6d9;border-radius:20px;transform:rotate(-2deg);box-shadow:0 14px 30px #1e5c391a}.bars{position:absolute;left:43px;bottom:39px;height:86px;display:flex;align-items:flex-end;gap:11px;z-index:2}.bar{width:21px;border-radius:7px 7px 3px 3px;background:#a2ddb7}.bar:nth-child(1){height:36px}.bar:nth-child(2){height:58px}.bar:nth-child(3){height:45px}.bar:nth-child(4){height:78px;background:var(--green)}.robot{position:absolute;right:37px;bottom:35px;font-size:66px;z-index:3}
.section-title{font-size:18px;font-weight:900;color:var(--ink);margin:4px 0 12px}[data-testid="stVerticalBlockBorderWrapper"]{background:white;border:1px solid var(--line);border-radius:18px;box-shadow:0 10px 28px #19442c0e}.tabs{display:flex;gap:26px;border-bottom:1px solid var(--line);padding:2px 2px 12px;margin-bottom:8px;color:#728078;font-size:13px;font-weight:800}.tab-active{color:var(--green);position:relative}.tab-active:after{content:"";position:absolute;left:0;right:0;bottom:-13px;height:2px;background:var(--green)}.stTextArea textarea{min-height:138px;border-radius:14px;border:1px solid #d9e5dd;background:#fbfdfb;font-size:15px;padding:15px}.stTextArea textarea:focus{border-color:var(--green);box-shadow:0 0 0 3px #168a4d1f}.stTextInput input{border-radius:12px;min-height:46px;border:1px solid #d9e5dd;background:#fbfdfb}.stTextInput input:focus{border-color:var(--green);box-shadow:0 0 0 3px #168a4d1f}.stButton button[kind="primary"]{min-height:48px;border:none;border-radius:12px;color:white;font-weight:850;background:linear-gradient(90deg,#168a4d,#20a65e)}.stButton button:not([kind="primary"]){min-height:48px;border-radius:12px;border:1px solid #d8e3dc;background:white;color:#536158;font-weight:750}
.metric-card{min-height:108px;display:flex;justify-content:space-between;align-items:center;background:white;border:1px solid var(--line);border-radius:18px;padding:20px;margin-bottom:12px;box-shadow:0 9px 26px #1a4a2e0e}.metric-label{font-size:12px;color:var(--muted);font-weight:750;margin-bottom:7px}.metric-value{font-size:24px;font-weight:950;color:var(--ink);letter-spacing:-.025em}.metric-icon{width:42px;height:42px;border-radius:13px;display:grid;place-items:center;background:var(--soft);font-size:20px}.metric-card.negative .metric-icon{background:#fff0ed}.metric-card.negative{border-color:#f3d9d3}.metric-card.profit{border-color:#cee8d7;background:linear-gradient(135deg,#fff,#f0faf4)}
.insight{padding:20px;border:1px solid #dde9e1;border-radius:18px;background:linear-gradient(135deg,#f7fcf8,#fff)}.badge{display:inline-flex;padding:6px 9px;border-radius:999px;background:#e4f5ea;color:#10683a;font-size:11px;font-weight:900;margin-bottom:10px}.insight-title{font-size:17px;font-weight:900;color:var(--ink);margin-bottom:7px}.insight-copy{font-size:13px;line-height:1.65;color:var(--muted)}[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:16px;overflow:hidden}.stDownloadButton button{min-height:48px;border:none;border-radius:12px;background:var(--dark);color:white;font-weight:850}.empty{padding:32px 22px;text-align:center;border:1px dashed #cfe0d5;border-radius:18px;background:#fbfdfb;color:var(--muted)}.empty-icon{font-size:36px}.footer-note{margin-top:24px;padding-top:18px;border-top:1px solid var(--line);text-align:center;color:#87938b;font-size:11px}[data-testid="stAlert"]{border-radius:13px}#MainMenu,footer{visibility:hidden}header{background:transparent}
@media(max-width:900px){.hero{padding:28px}.hero-title{font-size:32px}.hero-art,.profile{display:none}}
</style>
''', unsafe_allow_html=True)

# ── Session State (dipusatkan di sini, konsisten di semua halaman) ──
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0.0
if "last_chat_request_time" not in st.session_state:
    st.session_state.last_chat_request_time = 0.0
if "chat_question" not in st.session_state:
    st.session_state.chat_question = ""
if "chat_answer" not in st.session_state:
    st.session_state.chat_answer = ""
st.session_state.debug_mode = DEBUG_MODE

# ── Sidebar branding (nav fungsional di-generate otomatis oleh
#    st.navigation di bawah — bagian ini cuma header + kartu promo) ──
with st.sidebar:
    st.markdown(
        '''<div class="brand">
            <div class="brand-mark">🤖</div>
            <div>
                <div class="brand-title">CatatCuan AI</div>
                <div class="brand-sub">AI Financial Assistant</div>
            </div>
        </div>''',
        unsafe_allow_html=True,
    )

# ── Navigasi Multi-Halaman ───────────────────────────────────────────
pg = st.navigation(
    [
        st.Page(dashboard.render, title="Dashboard", icon="🏠", default=True, url_path="dashboard"),
        st.Page(transaksi.render, title="Transaksi", icon="🧾", url_path="transaksi"),
        st.Page(ai_insight.render, title="AI Insight", icon="✨", url_path="ai-insight"),
        st.Page(ai_chat.render, title="AI Chat", icon="💬", url_path="ai-chat"),
        st.Page(laporan.render, title="Laporan", icon="📄", url_path="laporan"),
        st.Page(pengaturan.render, title="Pengaturan", icon="⚙️", url_path="pengaturan"),
    ]
)

with st.sidebar:
    st.markdown(
        '''<div class="upgrade"><b>👑 Upgrade ke Pro</b>
        <p>Multi-user, laporan lanjutan, dan insight bisnis yang lebih lengkap akan hadir berikutnya.</p>
        </div><div class="version">CatatCuan AI · v1.0.0</div>''',
        unsafe_allow_html=True,
    )

pg.run()
