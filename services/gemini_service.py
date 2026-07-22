import json

from openai import OpenAI


MODEL_NAME = "llama-3.1-8b-instant"


class GeminiServiceError(Exception):
    """Tetap memakai nama lama agar app.py tidak perlu diubah."""


def _create_client(api_key: str) -> OpenAI:
    if not api_key:
        raise GeminiServiceError("GROQ_API_KEY belum tersedia.")

    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )


def analyze_transactions(api_key: str, user_input: str) -> dict:
    clean_input = str(user_input).strip()

    if not clean_input:
        return {"transactions": []}

    client = _create_client(api_key)

    prompt = f"""
Ubah cerita transaksi berikut menjadi JSON.

Aturan:
- Ambil semua transaksi yang disebutkan.
- Jangan mengarang nominal atau transaksi.
- Tipe hanya "income" atau "expense".
- Jika tanggal tidak disebutkan atau pengguna berkata "hari ini",
  gunakan "TODAY".
- Jika pengguna berkata "kemarin", gunakan "YESTERDAY".
- amount harus integer tanpa titik atau simbol mata uang.
- requires_confirmation bernilai true jika nominal atau maksud transaksi
  tidak jelas.
- Jawaban wajib berupa JSON valid saja, tanpa markdown.

Format:
{{
  "transactions": [
    {{
      "date": "TODAY",
      "type": "income",
      "category": "Penjualan",
      "description": "Penjualan kopi",
      "amount": 300000,
      "requires_confirmation": false
    }}
  ]
}}

TRANSAKSI PENGGUNA:
{clean_input}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Anda adalah CatatCuan AI, asisten pencatatan "
                        "keuangan UMKM Indonesia."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=1500,
        )

        raw_text = response.choices[0].message.content

        if not raw_text:
            raise GeminiServiceError(
                "AI tidak mengembalikan hasil transaksi."
            )

        result = json.loads(raw_text)

        transactions = result.get("transactions", [])

        if not isinstance(transactions, list):
            raise GeminiServiceError(
                "Format daftar transaksi tidak valid."
            )

        return {"transactions": transactions}

    except json.JSONDecodeError as error:
        raise GeminiServiceError(
            "AI mengembalikan format JSON yang tidak valid."
        ) from error

    except GeminiServiceError:
        raise

    except Exception as error:
        raise GeminiServiceError(
            "Layanan AI gagal memproses transaksi. Silakan coba lagi."
        ) from error


def ask_financial_assistant(
    api_key: str,
    question: str,
    transactions: list,
) -> str:
    clean_question = str(question).strip()

    if not clean_question:
        return "Silakan tulis pertanyaan terlebih dahulu."

    if not transactions:
        return (
            "Belum ada transaksi yang bisa dianalisis. "
            "Tambahkan transaksi terlebih dahulu."
        )

    client = _create_client(api_key)

    transaction_context = json.dumps(
        transactions[:500],
        ensure_ascii=False,
    )

    prompt = f"""
DATA TRANSAKSI:
{transaction_context}

PERTANYAAN:
{clean_question}

Jawab hanya berdasarkan data transaksi tersebut.

Aturan:
- Jangan mengarang angka atau fakta.
- Gunakan bahasa Indonesia sederhana.
- Gunakan format Rupiah.
- Jika data tidak cukup, katakan dengan jelas.
- Maksimal lima paragraf pendek atau lima poin.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Anda adalah CatatCuan AI, asisten analisis "
                        "keuangan UMKM Indonesia."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_tokens=1000,
        )

        answer = response.choices[0].message.content

        if not answer:
            raise GeminiServiceError(
                "AI tidak mengembalikan jawaban."
            )

        return answer.strip()

    except GeminiServiceError:
        raise

    except Exception as error:
        raise GeminiServiceError(
            "Layanan AI gagal memberikan analisis. Silakan coba lagi."
        ) from error
