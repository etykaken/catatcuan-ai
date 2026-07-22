import re
import threading
import time
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from services.gemini_service import analyze_transactions

MAX_INPUT_LENGTH = 1000
MAX_AMOUNT = 10_000_000_000
MAX_TRANSACTIONS_PER_REQUEST = 50
MAX_TOTAL_TRANSACTIONS = 5000
RATE_LIMIT_SECONDS = 3
GLOBAL_MAX_REQUESTS = 20
GLOBAL_WINDOW_SECONDS = 60
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@", "\t", "\r")
SECRET_LIKE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9\-_]{10,}|AIza[A-Za-z0-9\-_]{20,}|ya29\.[A-Za-z0-9\-_]{20,}|Bearer\s+[A-Za-z0-9\-_.]{10,})",
    re.IGNORECASE,
)
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
FAVICON_PATH = ASSETS_DIR / "favicon.png"

# Process-wide (bukan per-session) rate limiter. Ini lapisan pertahanan tambahan
# karena st.session_state hanya membatasi satu sesi/tab -- pengguna yang sama
# bisa membuka banyak tab/sesi untuk melewati RATE_LIMIT_SECONDS. Limiter ini
# dibagi ke semua sesi dalam satu proses server sehingga membatasi total beban
# ke API Gemini. Catatan: ini best-effort (reset jika proses restart / scaling
# multi-proses), bukan pengganti rate limiting di sisi gateway/reverse proxy.
_global_rate_lock = threading.Lock()
_global_request_log: list[float] = []


def check_global_rate_limit() -> bool:
    now = time.time()
    with _global_rate_lock:
        while _global_request_log and now - _global_request_log[0] > GLOBAL_WINDOW_SECONDS:
            _global_request_log.pop(0)
        if len(_global_request_log) >= GLOBAL_MAX_REQUESTS:
            return False
        _global_request_log.append(now)
        return True

try:
    DEBUG_MODE = bool(st.secrets.get("DEBUG_MODE", False))
except (FileNotFoundError, KeyError):
    DEBUG_MODE = False


def resolve_date(value: str) -> str:
    today = date.today()
    normalized = str(value).strip().upper()
    if normalized == "TODAY":
        return today.isoformat()
    if normalized == "YESTERDAY":
        return (today - timedelta(days=1)).isoformat()
    if normalized == "TOMORROW":
        return (today + timedelta(days=1)).isoformat()
    candidate = str(value).strip()
    if ISO_DATE_PATTERN.match(candidate):
        try:
            date.fromisoformat(candidate)
            return candidate
        except ValueError:
            pass
    return today.isoformat()


def format_rupiah(value: int | float) -> str:
    return f"Rp{value:,.0f}".replace(",", ".")


def coerce_amount(raw_amount) -> int | None:
    if isinstance(raw_amount, bool):
        return None
    if isinstance(raw_amount, int):
        return raw_amount
    if isinstance(raw_amount, float):
        return int(raw_amount) if raw_amount.is_integer() else None
    if isinstance(raw_amount, str):
        cleaned = raw_amount.strip()
        if not cleaned or not re.fullmatch(r"[0-9.,]+", cleaned):
            return None
        # BUG LAMA: replace(".", "").replace(",", "") melucuti titik & koma
        # sekaligus tanpa peduli mana pemisah ribuan dan mana pemisah desimal,
        # sehingga "300.000,50" (tiga ratus ribu koma lima puluh) akan salah
        # terbaca menjadi 30000050 (naik ~100x). Nominal di aplikasi ini
        # seharusnya bilangan bulat Rupiah (tanpa sen), jadi kita perlakukan
        # simbol terakhir sebagai pemisah desimal HANYA jika diikuti tepat
        # 1-2 digit di akhir string; jika bagian desimalnya bukan nol, kita
        # tolak nilainya (lebih aman gagal daripada diam-diam salah catat).
        last_dot, last_comma = cleaned.rfind("."), cleaned.rfind(",")
        decimal_pos = max(last_dot, last_comma)
        looks_decimal = decimal_pos != -1 and len(cleaned) - decimal_pos - 1 in (1, 2)
        if looks_decimal:
            integer_part = re.sub(r"[.,]", "", cleaned[:decimal_pos])
            decimal_part = cleaned[decimal_pos + 1:]
            if not integer_part.isdigit() or not decimal_part.isdigit():
                return None
            if int(decimal_part) != 0:
                return None
            digits = integer_part
        else:
            digits = re.sub(r"[.,]", "", cleaned)
        return int(digits) if digits.isdigit() else None
    return None


def coerce_bool(value) -> bool:
    # BUG LAMA: `"Ya" if item.get("requires_confirmation", False) else "Tidak"`
    # memakai truthiness Python langsung. Jika Gemini mengembalikan string
    # seperti "false" (bukan boolean asli), Python menganggapnya truthy
    # (string non-kosong) sehingga salah tercatat sebagai "Ya". Fungsi ini
    # menormalkan nilai dari luar (LLM/JSON) menjadi boolean yang benar.
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "ya"}
    return False


def sanitize_text_field(value, max_length: int) -> str:
    text = "".join(ch for ch in str(value).strip() if ch.isprintable() or ch == "\n")
    return text[:max_length]


def sanitize_excel_cell(text: str) -> str:
    text = str(text)
    return "'" + text if text.startswith(FORMULA_TRIGGER_CHARS) else text


def validate_transactions(raw_transactions: list) -> list:
    validated = []
    if not isinstance(raw_transactions, list):
        return validated
    for item in raw_transactions[:MAX_TRANSACTIONS_PER_REQUEST]:
        if not isinstance(item, dict) or item.get("type") not in {"income", "expense"}:
            continue
        amount = coerce_amount(item.get("amount"))
        if amount is None or amount <= 0 or amount > MAX_AMOUNT:
            continue
        validated.append({
            "Tanggal": resolve_date(item.get("date", "TODAY")),
            "Jenis": "Pemasukan" if item["type"] == "income" else "Pengeluaran",
            "Kategori": sanitize_excel_cell(sanitize_text_field(item.get("category", ""), 60)),
            "Keterangan": sanitize_excel_cell(sanitize_text_field(item.get("description", ""), 120)),
            "Nominal": amount,
            "Perlu Konfirmasi": "Ya" if coerce_bool(item.get("requires_confirmation", False)) else "Tidak",
        })
    return validated


def redact_secret_like_strings(text: str, api_key: str | None = None) -> str:
    if api_key:
        text = text.replace(api_key, "[REDACTED]")
    return SECRET_LIKE_PATTERN.sub("[REDACTED]", text)


def create_excel_report(dataframe, total_income, total_expense, net_result, expense_ratio) -> BytesIO:
    buffer = BytesIO()
    summary = pd.DataFrame({
        "Keterangan": ["Total Pemasukan", "Total Pengeluaran", "Laba/Rugi Bersih", "Status Keuangan", "Rasio Pengeluaran", "Jumlah Transaksi", "Tanggal Laporan"],
        "Nilai": [total_income, total_expense, net_result, "Laba" if net_result > 0 else "Rugi" if net_result < 0 else "Impas", f"{expense_ratio:.1f}%", len(dataframe), date.today().isoformat()],
    })
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Transaksi")
        summary.to_excel(writer, index=False, sheet_name="Ringkasan Keuangan")
        ws = writer.book["Transaksi"]
        sws = writer.book["Ringkasan Keuangan"]
        for col, width in {"A":15,"B":18,"C":22,"D":40,"E":18,"F":20}.items():
            ws.column_dimensions[col].width = width
        sws.column_dimensions["A"].width = 25
        sws.column_dimensions["B"].width = 25
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
        for cell in sws[1]:
            cell.font = cell.font.copy(bold=True)
        for row in range(2, ws.max_row + 1):
            ws[f"E{row}"].number_format = '"Rp"#,##0'
        for cell in ("B2", "B3", "B4"):
            sws[cell].number_format = '"Rp"#,##0'
        ws.freeze_panes = "A2"
        sws.freeze_panes = "A2"
    buffer.seek(0)
    return buffer


def metric_card(label: str, value: str, icon: str, extra: str = ""):
    st.markdown(f'''<div class="metric-card {extra}"><div><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div><div class="metric-icon">{icon}</div></div>''', unsafe_allow_html=True)


st.set_page_config(page_title="CatatCuan AI", page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else "💰", layout="wide", initial_sidebar_state="expanded")

st.markdown('''
<style>
:root{--green:#168a4d;--dark:#173d2c;--ink:#18231d;--muted:#6b776f;--line:#e2ebe5;--soft:#eaf7ef}
html,body,[class*="css"]{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}.stApp{background:#f7faf8}.block-container{max-width:1320px;padding-top:1.5rem;padding-bottom:4rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#f4fbf6,#edf7f0);border-right:1px solid var(--line)}[data-testid="stSidebar"] .block-container{padding:1.4rem 1rem}
.brand{display:flex;align-items:center;gap:10px;padding:5px 5px 20px}.brand-mark{width:43px;height:43px;border-radius:13px;display:grid;place-items:center;background:linear-gradient(135deg,#20a65e,#11723f);font-size:22px;box-shadow:0 8px 20px #168a4d38}.brand-title{font-size:18px;font-weight:900;color:var(--ink)}.brand-sub{font-size:11px;color:var(--muted)}
.side-label{font-size:10px;letter-spacing:.12em;color:#91a096;font-weight:800;padding:13px 10px 6px}.nav{padding:11px 12px;margin:3px 0;border-radius:12px;color:#526058;font-size:14px;font-weight:650}.nav.active{background:#dff2e6;color:#10683a}.upgrade{margin-top:25px;padding:16px;border-radius:16px;background:linear-gradient(145deg,#174c32,#0f3825);color:white}.upgrade b{font-size:14px}.upgrade p{font-size:11px;line-height:1.5;color:#cbe3d3}.version{margin-top:20px;color:#8b9890;font-size:11px}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}.kicker{font-size:13px;color:var(--muted)}.page-title{font-size:28px;font-weight:900;color:var(--ink);letter-spacing:-.03em}.profile{display:flex;align-items:center;gap:9px;padding:7px 11px 7px 8px;border:1px solid var(--line);border-radius:999px;background:white}.avatar{width:32px;height:32px;border-radius:50%;display:grid;place-items:center;background:#dff2e6}.profile-name{font-size:12px;font-weight:800}
.hero{display:flex;justify-content:space-between;align-items:center;min-height:230px;padding:34px 38px;margin-bottom:24px;border:1px solid #dceae1;border-radius:24px;background:radial-gradient(circle at 88% 20%,#4bbe7833,transparent 28%),linear-gradient(135deg,#fff,#effaf3);box-shadow:0 16px 40px #1e52330f;overflow:hidden}.hero-copy{max-width:720px}.eyebrow{font-size:13px;font-weight:850;letter-spacing:.08em;color:var(--green);text-transform:uppercase;margin-bottom:10px}.hero-title{font-size:40px;line-height:1.08;font-weight:950;color:var(--ink);letter-spacing:-.045em}.hero-title span{display:block;color:var(--green)}.hero-sub{font-size:15px;line-height:1.65;color:var(--muted);margin-top:14px;max-width:650px}.hero-art{position:relative;width:300px;height:180px;min-width:300px}.panel{position:absolute;inset:13px 16px 15px;background:#ffffffd9;border:1px solid #d2e6d9;border-radius:20px;transform:rotate(-2deg);box-shadow:0 14px 30px #1e5c391a}.bars{position:absolute;left:43px;bottom:39px;height:86px;display:flex;align-items:flex-end;gap:11px;z-index:2}.bar{width:21px;border-radius:7px 7px 3px 3px;background:#a2ddb7}.bar:nth-child(1){height:36px}.bar:nth-child(2){height:58px}.bar:nth-child(3){height:45px}.bar:nth-child(4){height:78px;background:var(--green)}.robot{position:absolute;right:37px;bottom:35px;font-size:66px;z-index:3}
.section-title{font-size:18px;font-weight:900;color:var(--ink);margin:4px 0 12px}[data-testid="stVerticalBlockBorderWrapper"]{background:white;border:1px solid var(--line);border-radius:18px;box-shadow:0 10px 28px #19442c0e}.tabs{display:flex;gap:26px;border-bottom:1px solid var(--line);padding:2px 2px 12px;margin-bottom:8px;color:#728078;font-size:13px;font-weight:800}.tab-active{color:var(--green);position:relative}.tab-active:after{content:"";position:absolute;left:0;right:0;bottom:-13px;height:2px;background:var(--green)}.stTextArea textarea{min-height:138px;border-radius:14px;border:1px solid #d9e5dd;background:#fbfdfb;font-size:15px;padding:15px}.stTextArea textarea:focus{border-color:var(--green);box-shadow:0 0 0 3px #168a4d1f}.stButton button[kind="primary"]{min-height:48px;border:none;border-radius:12px;color:white;font-weight:850;background:linear-gradient(90deg,#168a4d,#20a65e)}.stButton button:not([kind="primary"]){min-height:48px;border-radius:12px;border:1px solid #d8e3dc;background:white;color:#536158;font-weight:750}
.metric-card{min-height:108px;display:flex;justify-content:space-between;align-items:center;background:white;border:1px solid var(--line);border-radius:18px;padding:20px;margin-bottom:12px;box-shadow:0 9px 26px #1a4a2e0e}.metric-label{font-size:12px;color:var(--muted);font-weight:750;margin-bottom:7px}.metric-value{font-size:24px;font-weight:950;color:var(--ink);letter-spacing:-.025em}.metric-icon{width:42px;height:42px;border-radius:13px;display:grid;place-items:center;background:var(--soft);font-size:20px}.metric-card.negative .metric-icon{background:#fff0ed}.metric-card.profit{border-color:#cee8d7;background:linear-gradient(135deg,#fff,#f0faf4)}
.insight{padding:20px;border:1px solid #dde9e1;border-radius:18px;background:linear-gradient(135deg,#f7fcf8,#fff)}.badge{display:inline-flex;padding:6px 9px;border-radius:999px;background:#e4f5ea;color:#10683a;font-size:11px;font-weight:900;margin-bottom:10px}.insight-title{font-size:17px;font-weight:900;color:var(--ink);margin-bottom:7px}.insight-copy{font-size:13px;line-height:1.65;color:var(--muted)}[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:16px;overflow:hidden}.stDownloadButton button{min-height:48px;border:none;border-radius:12px;background:var(--dark);color:white;font-weight:850}.empty{padding:32px 22px;text-align:center;border:1px dashed #cfe0d5;border-radius:18px;background:#fbfdfb;color:var(--muted)}.empty-icon{font-size:36px}.footer-note{margin-top:24px;padding-top:18px;border-top:1px solid var(--line);text-align:center;color:#87938b;font-size:11px}[data-testid="stAlert"]{border-radius:13px}#MainMenu,footer{visibility:hidden}header{background:transparent}
@media(max-width:900px){.hero{padding:28px}.hero-title{font-size:32px}.hero-art,.profile{display:none}}
</style>
''', unsafe_allow_html=True)

if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0.0

with st.sidebar:
    st.markdown('''<div class="brand"><div class="brand-mark">🤖</div><div><div class="brand-title">CatatCuan AI</div><div class="brand-sub">AI Financial Assistant</div></div></div><div class="side-label">MENU UTAMA</div><div class="nav active">🏠 &nbsp; Dashboard</div><div class="nav">🧾 &nbsp; Transaksi</div><div class="nav">✨ &nbsp; AI Insight</div><div class="nav">💬 &nbsp; AI Chat</div><div class="nav">📄 &nbsp; Laporan</div><div class="side-label">LAINNYA</div><div class="nav">⚙️ &nbsp; Pengaturan</div><div class="upgrade"><b>👑 Upgrade ke Pro</b><p>Multi-user, laporan lanjutan, dan insight bisnis yang lebih lengkap akan hadir berikutnya.</p></div><div class="version">CatatCuan AI · v1.0.0</div>''', unsafe_allow_html=True)

st.markdown('''<div class="topbar"><div><div class="kicker">Dashboard keuangan usaha</div><div class="page-title">Selamat datang, Etyka! 👋</div></div><div class="profile"><div class="avatar">👩🏻</div><div class="profile-name">Etyka K.</div><div>⌄</div></div></div><div class="hero"><div class="hero-copy"><div class="eyebrow">CatatCuan AI</div><div class="hero-title">Catat pemasukan & pengeluaran<span>semudah bercerita</span></div><div class="hero-sub">AI membantu membaca transaksi, menyusunnya menjadi catatan keuangan, dan memberikan gambaran kondisi usaha dalam satu dashboard.</div></div><div class="hero-art"><div class="panel"></div><div class="bars"><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div></div><div class="robot">🤖</div></div></div>''', unsafe_allow_html=True)

if st.session_state.transactions:
    dataframe = pd.DataFrame(st.session_state.transactions)
    total_income = int(dataframe.loc[dataframe["Jenis"] == "Pemasukan", "Nominal"].sum())
    total_expense = int(dataframe.loc[dataframe["Jenis"] == "Pengeluaran", "Nominal"].sum())
else:
    dataframe = pd.DataFrame()
    total_income = total_expense = 0
net_result = total_income - total_expense
expense_ratio = (total_expense / total_income * 100) if total_income > 0 else 0

input_col, summary_col = st.columns([2.15, 1], gap="large")
with input_col:
    st.markdown('<div class="section-title">Catat transaksi baru</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="tabs"><div class="tab-active">✍️ Tulis Transaksi</div><div>📷 Upload Nota</div></div>', unsafe_allow_html=True)
        user_input = st.text_area("Ceritakan transaksi usaha kamu", placeholder="Contoh: Hari ini jual kopi Rp300.000, beli susu Rp80.000, dan bayar parkir Rp5.000.", height=138, max_chars=MAX_INPUT_LENGTH, label_visibility="collapsed")
        c1, c2 = st.columns([3, 1])
        with c1:
            analyze_button = st.button("✨ Analisis & Tambahkan Transaksi", type="primary", use_container_width=True)
        with c2:
            clear_button = st.button("🗑️ Hapus Semua", use_container_width=True)
with summary_col:
    st.markdown('<div class="section-title">Ringkasan Keuangan</div>', unsafe_allow_html=True)
    metric_card("Total Pemasukan", format_rupiah(total_income), "↗️")
    metric_card("Total Pengeluaran", format_rupiah(total_expense), "↘️", "negative")
    metric_card("Laba Bersih" if net_result >= 0 else "Kerugian", format_rupiah(net_result if net_result >= 0 else abs(net_result)), "💰", "profit")

if clear_button:
    st.session_state.transactions = []
    st.rerun()

if analyze_button:
    now = time.time()
    if now - st.session_state.last_request_time < RATE_LIMIT_SECONDS:
        st.warning("Mohon tunggu beberapa detik sebelum mengirim permintaan berikutnya.")
    elif not user_input.strip():
        st.warning("Tulis transaksi terlebih dahulu.")
    elif not check_global_rate_limit():
        st.warning("Sistem sedang menerima banyak permintaan. Silakan coba lagi sesaat lagi.")
    else:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except (FileNotFoundError, KeyError):
            st.error("GEMINI_API_KEY belum dipasang di Streamlit Secrets.")
        else:
            try:
                st.session_state.last_request_time = now
                with st.spinner("CatatCuan AI sedang membaca transaksi..."):
                    result = analyze_transactions(api_key=api_key, user_input=user_input.strip()[:MAX_INPUT_LENGTH])
                new_transactions = validate_transactions(result.get("transactions", []) if isinstance(result, dict) else [])
                if not new_transactions:
                    st.warning("Tidak ditemukan transaksi yang dapat dicatat.")
                else:
                    remaining = MAX_TOTAL_TRANSACTIONS - len(st.session_state.transactions)
                    if remaining <= 0:
                        st.warning(f"Riwayat transaksi sudah mencapai batas maksimum ({MAX_TOTAL_TRANSACTIONS}).")
                    else:
                        new_transactions = new_transactions[:remaining]
                        st.session_state.transactions.extend(new_transactions)
                        st.success(f"{len(new_transactions)} transaksi berhasil ditambahkan.")
                        st.rerun()
            except Exception as error:
                st.error("Transaksi gagal diproses. Silakan coba kembali.")
                if DEBUG_MODE:
                    with st.expander("Lihat detail error"):
                        st.code(redact_secret_like_strings(str(error), api_key))

st.markdown("<br>", unsafe_allow_html=True)
insight_col, chart_col = st.columns([1.2, 1], gap="large")
with insight_col:
    st.markdown('<div class="section-title">✨ AI Insight</div>', unsafe_allow_html=True)
    if not st.session_state.transactions:
        title, copy = "Mulai dari transaksi pertama", "Ceritakan pemasukan atau pengeluaran menggunakan bahasa sehari-hari. Dashboard akan diperbarui otomatis."
    elif net_result > 0:
        title, copy = "Usaha sedang mencatat laba", f"Laba bersih saat ini {format_rupiah(net_result)}. Pengeluaran memakai {expense_ratio:.1f}% dari total pemasukan."
    elif net_result < 0:
        title, copy = "Pengeluaran perlu diperhatikan", f"Usaha mencatat kerugian {format_rupiah(abs(net_result))}. Periksa kategori pengeluaran terbesar sebelum menambah biaya berikutnya."
    else:
        title, copy = "Posisi keuangan sedang impas", "Total pemasukan dan pengeluaran sama. Tambahkan transaksi berikutnya agar pola keuangan lebih terlihat."
    st.markdown(f'<div class="insight"><div class="badge">🤖 AI FINANCIAL CHECK</div><div class="insight-title">{title}</div><div class="insight-copy">{copy}</div></div>', unsafe_allow_html=True)
with chart_col:
    st.markdown('<div class="section-title">Arus Keuangan</div>', unsafe_allow_html=True)
    chart_df = pd.DataFrame({"Kategori": ["Pemasukan", "Pengeluaran"], "Nominal": [total_income, total_expense]}).set_index("Kategori")
    st.bar_chart(chart_df, use_container_width=True, height=220)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-title">🧾 Transaksi Terakhir</div>', unsafe_allow_html=True)
if st.session_state.transactions:
    dataframe = pd.DataFrame(st.session_state.transactions)
    display_df = dataframe.copy()
    display_df.index = display_df.index + 1
    display_df["Nominal"] = display_df["Nominal"].apply(format_rupiah)
    st.dataframe(display_df, use_container_width=True, hide_index=False)
    confirmations = int((dataframe["Perlu Konfirmasi"] == "Ya").sum())
    status_col, export_col = st.columns([1.3, 1], gap="large")
    with status_col:
        st.warning(f"{confirmations} transaksi perlu diperiksa kembali.") if confirmations else st.success("Semua transaksi terbaca tanpa memerlukan konfirmasi.")
    with export_col:
        excel_buffer = create_excel_report(dataframe, total_income, total_expense, net_result, expense_ratio)
        st.download_button("📥 Download Laporan Excel", excel_buffer, file_name=f"CatatCuanAI_Laporan_{date.today().isoformat()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
else:
    st.markdown('<div class="empty"><div class="empty-icon">🧾</div><strong>Belum ada transaksi</strong><br>Catat transaksi pertama kamu melalui kolom di atas.</div>', unsafe_allow_html=True)

st.markdown('<div class="footer-note">CatatCuan AI adalah MVP. Periksa kembali hasil pencatatan sebelum mengambil keputusan keuangan.</div>', unsafe_allow_html=True)
