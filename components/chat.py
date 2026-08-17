import html
from datetime import datetime

import streamlit as st

from config import MAX_CHAT_LENGTH


def _render_bubble(role: str, message: str) -> None:
    safe_message = html.escape(str(message)).replace("\n", "<br>")
    current_time = datetime.now().strftime("%H:%M")

    if role == "user":
        st.markdown(
            f"""
            <div class="chat-row chat-user-row">
                <div class="chat-bubble chat-user">
                    {safe_message}
                    <span class="chat-time">{current_time}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="chat-row chat-ai-row">
                <div class="chat-avatar">🤖</div>
                <div class="chat-bubble chat-ai">
                    {safe_message}
                    <span class="chat-time">{current_time}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_chat() -> tuple[str, bool, bool]:
    with st.container(border=True, key="chat_card"):
        header_left, header_right = st.columns([4, 1])

        with header_left:
            st.markdown(
                """
                <div class="section-title">
                    <span class="section-number">3</span>
                    💬 Tanya CatatCuan AI
                </div>
                """,
                unsafe_allow_html=True,
            )

        with header_right:
            clear_button = st.button(
                "Bersihkan Chat",
                use_container_width=True,
            )

        input_column, result_column = st.columns([1, 1], gap="medium")

        with input_column:
            question = st.text_area(
                "Pertanyaan",
                placeholder="Contoh: Apakah pengeluaran saya sehat?",
                height=105,
                max_chars=MAX_CHAT_LENGTH,
                label_visibility="collapsed",
            )
            ask_button = st.button(
                "➤ Tanya AI",
                type="primary",
                use_container_width=True,
            )

        with result_column:
            if st.session_state.chat_history:
                for item in st.session_state.chat_history[-6:]:
                    _render_bubble(item["role"], item["message"])
            else:
                st.markdown(
                    '<div class="empty-box">Belum ada percakapan.</div>',
                    unsafe_allow_html=True,
                )

    return question, ask_button, clear_button
