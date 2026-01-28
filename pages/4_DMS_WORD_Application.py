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
    import streamlit as st
    
    # Temporarily override set_page_config to prevent conflicts
    original_set_page_config = st.set_page_config
    st.set_page_config = lambda *args, **kwargs: None
    
    try:
        # Change to the app directory to ensure relative paths work correctly
        original_cwd = os.getcwd()
        os.chdir(app_dir)
        
        # Execute the DMS app file directly to run its Streamlit components
        with open("streamlit_app.py", "r", encoding="utf-8") as f:
            code = f.read()
            # Execute the code in the current namespace to run the Streamlit elements
            exec(code, globals())
        
        # Restore original working directory
        os.chdir(original_cwd)
        
    except Exception as e:
        # Restore original function in case of error
        st.set_page_config = original_set_page_config
        os.chdir(original_cwd)  # Make sure to restore CWD even if there's an error
        st.error(f"Ошибка при запуске приложения DMS: {e}")
        # Print stack trace for debugging
        import traceback
        st.code(traceback.format_exc())
        st.info(f"App dir: {app_dir}")