import streamlit as st
from supabase import Client, create_client


class SupabaseServiceError(Exception):
    pass


def get_supabase_client() -> Client:
    url = str(st.secrets.get("SUPABASE_URL", "")).strip()
    key = str(st.secrets.get("SUPABASE_KEY", "")).strip()

    if not url:
        raise SupabaseServiceError(
            "SUPABASE_URL belum tersedia di Streamlit Secrets."
        )
    if not key:
        raise SupabaseServiceError(
            "SUPABASE_KEY belum tersedia di Streamlit Secrets."
        )
    if not url.startswith("https://"):
        raise SupabaseServiceError(
            "Format SUPABASE_URL tidak valid."
        )

    try:
        return create_client(url, key)
    except Exception as error:
        raise SupabaseServiceError(
            f"Supabase client gagal dibuat: "
            f"{type(error).__name__}: {error}"
        ) from error


def test_connection() -> bool:
    client = get_supabase_client()
    try:
        client.table("transactions").select("id").limit(1).execute()
        return True
    except Exception as error:
        raise SupabaseServiceError(
            f"Koneksi database gagal: "
            f"{type(error).__name__}: {error}"
        ) from error
