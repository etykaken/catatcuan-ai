import json

from google import genai
from google.genai import types


MODEL_NAME = "gemini-3.5-flash"

SYSTEM_INSTRUCTION = """
Anda adalah CatatCuan AI, asisten pencatatan keuangan untuk UMKM Indonesia.
Ubah cerita transaksi pengguna menjadi JSON terstruktur.
Aturan:
1. Ambil semua transaksi yang disebutkan.
2. Jangan mengarang transaksi atau nominal.
3. Jenis transaksi hanya "income" atau "expense".
4. Jika pengguna mengatakan "hari ini" atau tidak menyebut tanggal,
   gunakan "TODAY".
5. Jika pengguna mengatakan "kemarin", gunakan "YESTERDAY".
6. Jangan menebak tanggal kalender saat ini.
7. Keluarkan JSON saja.
"""

FINANCIAL_ASSISTANT_INSTRUCTION = """
Anda adalah CatatCuan AI, asisten analisis keuangan untuk UMKM Indonesia.
Jawab pertanyaan pengguna hanya berdasarkan data transaksi yang diberikan.
Aturan:
1. Jangan mengarang angka, transaksi, tren, atau fakta.
2. Gunakan bahasa Indonesia yang sederhana dan mudah dipahami pelaku UMKM.
3. Jawab langsung ke inti pertanyaan.
4. Gunakan format Rupiah untuk nominal.
5. Jika data tidak cukup untuk menjawab, katakan bahwa datanya belum cukup.
6. Jangan memberikan kepastian mutlak tentang kesehatan bisnis hanya dari sedikit data.
7. Jika memberikan saran, buat saran yang realistis dan dapat dilakukan.
8. Maksimal 5 paragraf pendek atau 5 poin.
"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "transactions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["income", "expense"],
                    },
                    "category": {"type": "string"},
                    "description": {"type": "string"},
                    "amount": {"type": "integer"},
                    "requires_confirmation": {"type": "boolean"},
                },
                "required": [
                    "date",
                    "type",
                    "category",
                    "description",
                    "amount",
                    "requires_confirmation",
                ],
            },
        }
    },
    "required": ["transactions"],
}


class GeminiServiceError(Exception):
    """Error khusus service Gemini, dengan pesan yang lebih jelas dari
    exception mentah SDK. Memudahkan debugging tanpa membocorkan detail
    internal ke end user (app.py tetap menampilkan pesan generik ke user,
    tapi pesan di sini lebih berguna saat DEBUG_MODE aktif)."""


def _extract_text_or_raise(response, context: str) -> str:
    """Ambil teks dari response Gemini, dengan validasi eksplisit.

    Tanpa fungsi ini, response yang kosong/terpotong (misalnya karena
    thinking token menghabiskan budget max_output_tokens, atau konten
    diblokir filter keamanan) akan membuat `json.loads(None)` melempar
    TypeError yang membingungkan. Di sini errornya dibuat jelas.
    """
    candidates = getattr(response, "candidates", None)

    if not candidates:
        raise GeminiServiceError(
            f"{context}: tidak ada kandidat respons dari Gemini "
            "(kemungkinan diblokir filter keamanan)."
        )

    finish_reason = getattr(candidates[0], "finish_reason", None)

    text = response.text

    if not text:
        raise GeminiServiceError(
            f"{context}: respons kosong dari Gemini "
            f"(finish_reason={finish_reason}). Ini sering terjadi karena "
            "token 'thinking' menghabiskan budget max_output_tokens — "
            "coba naikkan max_output_tokens atau turunkan thinking_level."
        )

    return text


def analyze_transactions(api_key: str, user_input: str) -> dict:
    client = genai.Client(api_key=api_key)

    import time

for i in range(3):
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
                thinking_config=types.ThinkingConfig(
                    thinking_level="low",
                ),
                max_output_tokens=2048,
                temperature=0.1,
            ),
        )
        break

    except Exception as e:
        if "503" in str(e) and i < 2:
            time.sleep(2)
            continue
        raise
        model=MODEL_NAME,
        contents=user_input,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
            # Tugas ini ekstraksi terstruktur sederhana yang sudah
            # dikunci oleh response_schema — tidak butuh reasoning
            # panjang. Thinking dimatikan (level rendah) supaya seluruh
            # token output dipakai untuk hasil JSON, bukan "mikir".
            thinking_config=types.ThinkingConfig(
                thinking_level="low",
            ),
            # Dinaikkan dari 1200 sebagai buffer aman untuk input
            # dengan banyak transaksi sekaligus.
            max_output_tokens=2048,
            temperature=0.1,
        ),
    )

    raw_text = _extract_text_or_raise(response, "analyze_transactions")

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise GeminiServiceError(
            f"analyze_transactions: gagal mem-parsing JSON dari Gemini "
            f"({error})."
        ) from error


def ask_financial_assistant(
    api_key: str,
    question: str,
    transactions: list,
) -> str:
    """Menjawab pertanyaan berdasarkan riwayat transaksi pengguna."""
    if not transactions:
        return (
            "Belum ada transaksi yang bisa dianalisis. "
            "Tambahkan transaksi terlebih dahulu."
        )

    safe_transactions = transactions[:500]

    transaction_context = json.dumps(
        safe_transactions,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    prompt = f"""
DATA TRANSAKSI:
{transaction_context}

PERTANYAAN PENGGUNA:
{question}

Analisis dan jawab hanya berdasarkan data transaksi di atas.
"""

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=FINANCIAL_ASSISTANT_INSTRUCTION,
            temperature=0.2,
            # Butuh sedikit reasoning untuk insight kualitatif, tapi
            # tetap dibatasi supaya tidak menghabiskan budget output.
            thinking_config=types.ThinkingConfig(
                thinking_level="low",
            ),
            max_output_tokens=1200,
        ),
    )

    answer = _extract_text_or_raise(response, "ask_financial_assistant")

    return answer.strip()
