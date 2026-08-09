import streamlit as st

from config import MAX_INPUT_LENGTH


def render_transaction_input() -> tuple[str, bool]:
    language = st.session_state.get("language", "id")

    if language == "id":
        section_title = "Catat transaksi"
        helper_text = (
            "Ceritakan apa yang terjadi dengan usahamu hari ini. "
            "CatatCuan akan membantu merapikan transaksinya."
        )
        question_text = "Apa yang terjadi hari ini?"
        placeholder_text = (
            "Contoh:\n"
            "Hari ini jual 3 kopi total 75 ribu, "
            "beli susu 25 ribu, dan bayar listrik 150 ribu."
        )
        note_text = (
            "Kamu tidak perlu menggunakan istilah akuntansi. "
            "Ceritakan saja seperti biasa."
        )
        button_text = "Catat transaksi →"

    else:
        section_title = "Record transactions"
        helper_text = (
            "Tell us what happened in your business today. "
            "CatatCuan will help organize the transactions."
        )
        question_text = "What happened today?"
        placeholder_text = (
            "Example:\n"
            "Sold 3 coffees for a total of Rp75,000, "
            "bought milk for Rp25,000, and paid "
            "Rp150,000 for electricity."
        )
        note_text = (
            "You don't need to use accounting terms. "
            "Just describe it naturally."
        )
        button_text = "Record transactions →"

    with st.container(border=True):
        st.markdown(f"### 1  {section_title}")

        st.caption(helper_text)

        st.write("")

        st.markdown(f"**{question_text}**")

        transaction_text = st.text_area(
            "Transaction",
            placeholder=placeholder_text,
            height=150,
            max_chars=MAX_INPUT_LENGTH,
            label_visibility="collapsed",
            key="transaction_input_text",
        )

        st.caption(note_text)

        analyze_button = st.button(
            button_text,
            type="primary",
            use_container_width=True,
            key="analyze_transaction_button",
        )

    return transaction_text, analyze_button
