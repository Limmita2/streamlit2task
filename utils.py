import streamlit as st


def remove_max_width():
    """
    Прибирає обмеження max-width для контейнера основного блоку Streamlit.
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