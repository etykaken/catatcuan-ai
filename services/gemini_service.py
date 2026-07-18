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


def analyze_transactions(api_key: str, user_input: str) -> dict:
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_input,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
            max_output_tokens=1200,
        ),
    )

    return json.loads(response.text)


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
            max_output_tokens=700,
        ),
    )

    answer = response.text

    if not answer:
        return (
            "CatatCuan AI belum dapat menghasilkan jawaban. "
            "Silakan coba pertanyaan lain."
        )

    return answer.strip()
