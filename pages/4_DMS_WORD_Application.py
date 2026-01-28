import sys
import os
from pathlib import Path

# --- PATH SETUP ---
# Get the root directory (parent of 'pages')
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
app_dir = os.path.join(root_dir, "DMS_v_WORD")

# Add to sys.path to allow imports
if app_dir not in sys.path:
    sys.path.append(app_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Check if required dependencies are available
try:
    import fitz  # PyMuPDF
    dependencies_available = True
except ImportError:
    dependencies_available = False

if not dependencies_available:
    import streamlit as st
    st.title("DMS v WORD")
    st.error("⚠️ Отсутствуют необходимые зависимости для запуска приложения")
    
    st.write("Для установки зависимостей выполните команду:")
    st.code("pip install pymupdf", language="bash")
    
    st.write("Или установите все зависимости из файла requirements.txt:")
    st.code("pip install -r DMS_v_WORD/requirements.txt", language="bash")
    
    if st.button("🏠 Вернуться на главную"):
        st.switch_page("Home.py")
else:
    # Import and run the DMS application
    try:
        import DMS_v_WORD.streamlit_app  # This will run the app since it has direct Streamlit calls
        
    except Exception as e:
        import streamlit as st
        st.error(f"Ошибка при запуске приложения DMS: {e}")
        # Print stack trace for debugging
        import traceback
        st.code(traceback.format_exc())
        st.info(f"App dir: {app_dir}")