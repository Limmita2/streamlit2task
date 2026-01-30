import streamlit as st


def remove_max_width():
    """
    Убирает ограничение max-width для контейнера основного блока Streamlit.
    """
    st.markdown(
        """
        <style>
        .stMainBlockContainer {
            max-width: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )