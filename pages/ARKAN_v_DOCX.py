import sys
import os
from pathlib import Path

# --- PATH SETUP ---
# Get the root directory (parent of 'pages')
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
app_dir = os.path.join(root_dir, "ARKAN_v_DOCX")

# Add to sys.path to allow imports
if app_dir not in sys.path:
    sys.path.append(app_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Check if required dependencies are available
try:
    import streamlit
    import openpyxl
    import docx
    dependencies_available = True
except ImportError:
    dependencies_available = False

if not dependencies_available:
    import streamlit as st
    st.title("ARKAN v DOCX")
    st.error("⚠️ Отсутствуют необходимые зависимости для запуска приложения")
    
    st.write("Для установки зависимостей выполните команду:")
    st.code("pip install -r ARKAN_v_DOCX/requirements.txt", language="bash")
    
    st.write("Или установите каждую зависимость отдельно:")
    st.code("pip install streamlit openpyxl python-docx", language="bash")
    
    if st.button("🏠 Вернуться на главную"):
        st.switch_page("Home.py")
else:
    # Import and run the ARKAN application
    import streamlit as st
    
    # Temporarily override set_page_config to prevent conflicts
    original_set_page_config = st.set_page_config
    st.set_page_config = lambda *args, **kwargs: None
    
    try:
        # Change to the app directory to ensure relative paths work correctly
        original_cwd = os.getcwd()
        os.chdir(app_dir)
        
        # Execute the ARKAN app file directly to run its Streamlit components
        with open("excel_to_word_app.py", "r", encoding="utf-8") as f:
            code = f.read()
            # Execute the code in the current namespace to run the Streamlit elements
            exec(code, globals())
        
        # Restore original working directory
        os.chdir(original_cwd)
        
    except Exception as e:
        # Restore original function in case of error
        st.set_page_config = original_set_page_config
        os.chdir(original_cwd)  # Make sure to restore CWD even if there's an error
        st.error(f"Ошибка при запуске приложения ARKAN: {e}")
        # Print stack trace for debugging
        import traceback
        st.code(traceback.format_exc())
        st.info(f"App dir: {app_dir}")