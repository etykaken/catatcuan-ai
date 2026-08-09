import streamlit as st
from supabase import Client, create_client


class SupabaseServiceError(Exception):
    pass


def get_supabase_client() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]

        return create_client(url, key)

    except Exception as error:
        raise SupabaseServiceError(
            "Supabase gagal diinisialisasi."
        ) from error


def test_connection() -> bool:
    client = get_supabase_client()

    try:
        client.table("transactions").select("id").limit(1).execute()
        return True

    except Exception as error:
        raise SupabaseServiceError(
            "Koneksi database gagal."
        ) from error
