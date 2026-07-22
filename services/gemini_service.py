import json
import time

from google import genai
from google.genai import types


MODEL_NAME = "gemini-2.5-flash-lite"

SYSTEM_INSTRUCTION = """
Anda adalah CatatCuan AI, asisten pencatatan keuangan untuk UMKM Indonesia.

Tugas Anda:
- Ubah cerita transaksi pengguna menjadi data JSON terstruktur.
- Ambil semua transaksi yang disebutkan.
- Jangan mengarang transaksi atau nominal.
- Jenis transaksi hanya "income" atau "expense".
- Jika tanggal tidak disebutkan atau pengguna mengatakan "hari ini", gunakan "TODAY".
- Jika pengguna mengatakan "kemarin", gunakan "YESTERDAY".
- Gunakan kategori yang singkat dan relevan.
- Keluarkan JSON saja.
"""

FINANCIAL_ASSISTANT_INSTRUCTION = """
Anda adalah CatatCuan AI, asisten analisis keuangan untuk UMKM Indonesia.

Aturan:
- Jawab hanya berdasarkan data transaksi yang diberikan.
- Jangan mengarang angka, transaksi, tren, atau fakta.
- Gunakan bahasa Indonesia yang sederhana.
- Gunakan format Rupiah untuk nominal.
- Jika data belum cukup, katakan dengan jelas.
- Maksimal 5 poin atau 5 paragraf pendek.
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
    """Error aman untuk ditampilkan atau dicatat oleh aplikasi."""


def _get_response_text(response, context: str) -> str:
    text = getattr(response, "text", None)

    if not text:
        raise GeminiServiceError(
            f"{context}: Gemini tidak mengembalikan jawaban."
        )

    return text.strip()


def _generate_with_retry(
    client,
    *,
    contents: str,
    config: types.GenerateContentConfig,
):
    last_error = None

    for attempt in range(3):
        try:
            return client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=config,
            )
        except Exception as error:
            last_error = error
            message = str(error).lower()

            temporary_error = any(
                marker in message
                for marker in (
                    "503",
                    "unavailable",
                    "high demand",
                    "429",
                    "resource exhausted",
                )
            )

            if temporary_error and attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue

            break

    raise GeminiServiceError(
        "Layanan Gemini sedang sibuk. Silakan coba lagi beberapa saat."
    ) from last_error


def analyze_transactions(api_key: str, user_input: str) -> dict:
    if not api_key:
        raise GeminiServiceError("GEMINI_API_KEY belum tersedia.")

    clean_input = str(user_input).strip()

    if not clean_input:
        return {"transactions": []}

    client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=RESPONSE_SCHEMA,
        temperature=0.1,
        max_output_tokens=2048,
    )

    response = _generate_with_retry(
        client,
        contents=clean_input,
        config=config,
    )

    raw_text = _get_response_text(
        response,
        "analyze_transactions",
    )

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise GeminiServiceError(
            "Gemini mengembalikan format transaksi yang tidak valid."
        ) from error

    if not isinstance(parsed, dict):
        raise GeminiServiceError(
            "Format respons transaksi tidak sesuai."
        )

    transactions = parsed.get("transactions", [])

    if not isinstance(transactions, list):
        raise GeminiServiceError(
            "Daftar transaksi dari Gemini tidak valid."
        )

    return {"transactions": transactions}


def ask_financial_assistant(
    api_key: str,
    question: str,
    transactions: list,
) -> str:
    if not api_key:
        raise GeminiServiceError("GEMINI_API_KEY belum tersedia.")

    clean_question = str(question).strip()

    if not clean_question:
        return "Silakan tulis pertanyaan terlebih dahulu."

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

PERTANYAAN:
{clean_question}

Jawab hanya berdasarkan data transaksi di atas.
"""

    client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        system_instruction=FINANCIAL_ASSISTANT_INSTRUCTION,
        temperature=0.2,
        max_output_tokens=1200,
    )

    response = _generate_with_retry(
        client,
        contents=prompt,
        config=config,
    )

    return _get_response_text(
        response,
        "ask_financial_assistant",
    )
