import streamlit as st
from supabase import Client, create_client


class SupabaseServiceError(Exception):
    """Error khusus koneksi dan autentikasi Supabase."""


def get_supabase_client() -> Client:
    try:
        supabase_config = st.secrets["connections"]["supabase"]

        url = str(
            supabase_config["SUPABASE_URL"]
        ).strip()

        key = str(
            supabase_config["SUPABASE_KEY"]
        ).strip()

    except (KeyError, FileNotFoundError) as error:
        raise SupabaseServiceError(
            "Konfigurasi Supabase belum tersedia."
        ) from error

    if not url:
        raise SupabaseServiceError(
            "SUPABASE_URL belum tersedia."
        )

    if not key:
        raise SupabaseServiceError(
            "SUPABASE_KEY belum tersedia."
        )

    if not url.startswith("https://"):
        raise SupabaseServiceError(
            "Format SUPABASE_URL tidak valid."
        )

    try:
        return create_client(
            url,
            key,
        )

    except Exception as error:
        raise SupabaseServiceError(
            "CatatCuan gagal terhubung ke layanan akun."
        ) from error


def sign_up(
    email: str,
    password: str,
):
    client = get_supabase_client()

    try:
        response = client.auth.sign_up(
            {
                "email": email,
                "password": password,
            }
        )

        if not response.user:
            raise SupabaseServiceError(
                "Akun tidak berhasil dibuat."
            )

        return response

    except SupabaseServiceError:
        raise

    except Exception as error:
        message = str(error).lower()

        if "already registered" in message:
            raise SupabaseServiceError(
                "Email ini sudah terdaftar."
            ) from error

        if "password" in message:
            raise SupabaseServiceError(
                "Password belum memenuhi persyaratan."
            ) from error

        if "email" in message:
            raise SupabaseServiceError(
                "Alamat email tidak valid."
            ) from error

        raise SupabaseServiceError(
            "Akun belum berhasil dibuat. Silakan coba lagi."
        ) from error


def sign_in(
    email: str,
    password: str,
):
    client = get_supabase_client()

    try:
        response = client.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )

        if not response.user:
            raise SupabaseServiceError(
                "Email atau password tidak sesuai."
            )

        return response

    except SupabaseServiceError:
        raise

    except Exception as error:
        message = str(error).lower()

        if (
            "invalid login credentials" in message
            or "invalid credentials" in message
        ):
            raise SupabaseServiceError(
                "Email atau password tidak sesuai."
            ) from error

        if "email not confirmed" in message:
            raise SupabaseServiceError(
                "Email belum dikonfirmasi. "
                "Silakan cek inbox terlebih dahulu."
            ) from error

        raise SupabaseServiceError(
            "CatatCuan belum berhasil masuk. "
            "Silakan coba lagi."
        ) from error


def sign_out() -> None:
    client = get_supabase_client()

    try:
        client.auth.sign_out()

    except Exception as error:
        raise SupabaseServiceError(
            "Gagal keluar dari akun."
        ) from error
