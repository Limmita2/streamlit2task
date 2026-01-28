import streamlit as st
from pathlib import Path

st.title("DMS v WORD")
st.info("Приложение DMS v WORD запускается отдельно.")

st.write("Для запуска приложения откройте терминал и выполните команду:")
st.code("cd DMS_v_WORD && streamlit run streamlit_app.py", language="bash")

st.write("После запуска приложение будет доступно по адресу: http://localhost:8501")

# Add a button to go back to the main page
if st.button("🏠 Вернуться на главную"):
    st.switch_page("Home.py")