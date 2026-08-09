TRANSLATIONS = {
    "id": {
        # General
        "language": "Bahasa",
        "indonesian": "Indonesia",
        "english": "English",

        # Auth
        "login_signup": "Masuk / Buat akun",
        "back_home": "← Kembali ke CatatCuan",
        "login": "Masuk",
        "signup": "Buat akun",
        "welcome_back": "Selamat datang kembali",
        "login_helper": "Masuk untuk melanjutkan pencatatan usahamu.",
        "start_catatcuan": "Mulai pakai CatatCuan",
        "signup_helper": "Buat akun untuk menyimpan dan melanjutkan pencatatan usahamu.",
        "email": "Email",
        "password": "Password",
        "confirm_password": "Konfirmasi password",
        "login_button": "Masuk →",
        "signup_button": "Buat akun →",

        # Main
        "transaction": "Catat Transaksi",
        "transaction_helper": "Tulis transaksi harian dengan bahasa alami.",
        "analyze": "Analisis & Tambahkan Transaksi",
        "income": "Pemasukan",
        "expense": "Pengeluaran",
        "balance": "Selisih",
        "history": "Riwayat Transaksi",
        "delete_all": "Hapus semua data",

        # Brand
        "brand_message": "Catat keuangan semudah bercerita.",
    },

    "en": {
        # General
        "language": "Language",
        "indonesian": "Indonesian",
        "english": "English",

        # Auth
        "login_signup": "Sign in / Create account",
        "back_home": "← Back to CatatCuan",
        "login": "Sign in",
        "signup": "Create account",
        "welcome_back": "Welcome back",
        "login_helper": "Sign in to continue managing your business finances.",
        "start_catatcuan": "Get started with CatatCuan",
        "signup_helper": "Create an account to save and continue tracking your business finances.",
        "email": "Email",
        "password": "Password",
        "confirm_password": "Confirm password",
        "login_button": "Sign in →",
        "signup_button": "Create account →",

        # Main
        "transaction": "Record Transaction",
        "transaction_helper": "Describe your daily transactions in natural language.",
        "analyze": "Analyze & Add Transactions",
        "income": "Income",
        "expense": "Expenses",
        "balance": "Net Balance",
        "history": "Transaction History",
        "delete_all": "Delete all data",

        # Brand
        "brand_message": "Track your finances as naturally as telling a story.",
    },
}


def t(key: str, language: str = "id") -> str:
    selected_language = (
        language
        if language in TRANSLATIONS
        else "id"
    )

    return TRANSLATIONS[
        selected_language
    ].get(
        key,
        TRANSLATIONS["id"].get(key, key),
    )
