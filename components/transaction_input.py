import streamlit as st

from config import MAX_INPUT_LENGTH


def render_transaction_input() -> tuple[str, bool]:
    with st.container(border=True):
        st.markdown(
            """
            <div class="section-title">
                <span class="section-number">1</span>
                Catat transaksi
            </div>

            <div class="section-helper">
                Ceritakan apa yang terjadi dengan usahamu hari ini.
                CatatCuan akan membantu merapikan transaksinya.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="
                margin: 14px 0 8px;
                font-size: 13px;
                font-weight: 700;
                color: #343a40;
            ">
                Apa yang terjadi hari ini?
            </div>
            """,
            unsafe_allow_html=True,
        )

        transaction_text = st.text_area(
            "Transaksi",
            placeholder=(
                "Contoh:\n"
                "Hari ini jual 3 kopi total 75 ribu, "
                "beli susu 25 ribu, dan bayar listrik 150 ribu."
            ),
            height=150,
            max_chars=MAX_INPUT_LENGTH,
            label_visibility="collapsed",
        )

        st.markdown(
            """
            <div style="
                margin-top: -4px;
                margin-bottom: 12px;
                color: #8a8a87;
                font-size: 11px;
                line-height: 1.5;
            ">
                Kamu tidak perlu menggunakan istilah akuntansi.
                Ceritakan saja seperti biasa.
            </div>
            """,
            unsafe_allow_html=True,
        )

        analyze_button = st.button(
            "Catat transaksi →",
            type="primary",
            use_container_width=True,
        )

    return transaction_text, analyze_button
