import streamlit as st
import sys
import os

# --- PATH SETUP ---
# Get the root directory (parent of 'pages')
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
app_dir = os.path.join(root_dir, "MANY_PDF_v_PERSON")

# Add to sys.path to allow imports
if app_dir not in sys.path:
    # Insert at beginning to ensure local modules like 'pdf_processor' are found
    sys.path.insert(0, app_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# --- CONFIG ---
# Set config explicitly here
st.set_page_config(page_title="Генератор досьє з PDF", page_icon="📄", layout="wide")

from utils import remove_max_width
remove_max_width()

# --- IMPORT & RUN ---
try:
    # Change working directory to app dir so it can find 'default_avatar.png' etc.
    os.chdir(app_dir)

    # Попробуем импортировать напрямую, если находимся в подкаталоге
    try:
        import app as person_app
    except ImportError:
        # Если прямой импорт не работает, пробуем с указанием пути
        import MANY_PDF_v_PERSON.app as person_app

    # Run the main function
    if hasattr(person_app, 'main'):
        person_app.main()
    else:
        st.error("В модуле приложения не найдена функция main().")

except Exception as e:
    st.error(f"Ошибка при запуске приложения: {e}")
    import traceback
    st.code(traceback.format_exc())
    st.info(f"App dir: {app_dir}")
finally:
    # Reset CWD to root (optional, but good practice if other pages rely on it)
    # However, Streamlit reruns might reset it anyway or cause issues if we change it back mid-run inside a component.
    # For a multipage app, it is often safer to keep CWD or handle paths absolutely.
    # But since this app uses relative 'default_avatar.png' etc., changing CWD is the easiest fix.
    pass
