import json

from openai import OpenAI

MODEL_NAME = "llama-3.1-8b-instant"


class AIServiceError(Exception):
    """Error khusus layanan AI."""


def _create_client(api_key: str) -> OpenAI:
    if not api_key:
        raise AIServiceError("GROQ_API_KEY belum tersedia.")

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
Ubah cerita transaksi berikut menjadi JSON valid.

Aturan:
- Ambil semua transaksi.
- Jangan mengarang nominal.
- type hanya income atau expense.
- Jika tanggal tidak disebutkan atau hari ini, gunakan TODAY.
- Jika kemarin, gunakan YESTERDAY.
- amount harus integer.
- requires_confirmation true jika informasi tidak jelas.
- Jawab JSON saja.

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

TRANSAKSI:
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
                        "keuangan untuk UMKM Indonesia."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=1500,
        )

        content = response.choices[0].message.content
        if not content:
            raise AIServiceError("AI tidak mengembalikan hasil.")

        result = json.loads(content)
        transactions = result.get("transactions", [])

        if not isinstance(transactions, list):
            raise AIServiceError("Format daftar transaksi tidak valid.")

        return {"transactions": transactions}

    except json.JSONDecodeError as error:
        raise AIServiceError("Format JSON dari AI tidak valid.") from error
    except AIServiceError:
        raise
    except Exception as error:
        raise AIServiceError(
            "Layanan AI gagal memproses transaksi."
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
        return "Belum ada transaksi yang bisa dianalisis."

    client = _create_client(api_key)
    context = json.dumps(
        transactions[:500],
        ensure_ascii=False,
        separators=(",", ":"),
    )

    prompt = f"""
DATA TRANSAKSI:
{context}

PERTANYAAN:
{clean_question}

Jawab hanya berdasarkan data di atas.
Gunakan bahasa Indonesia sederhana dan format Rupiah.
Jangan mengarang angka. Maksimal lima poin pendek.
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
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1000,
        )

        answer = response.choices[0].message.content
        if not answer:
            raise AIServiceError("AI tidak mengembalikan jawaban.")

        return answer.strip()

    except AIServiceError:
        raise
    except Exception as error:
        raise AIServiceError(
            "Layanan AI gagal memberikan analisis."
        ) from error
