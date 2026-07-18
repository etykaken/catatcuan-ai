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
