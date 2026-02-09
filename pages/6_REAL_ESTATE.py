import streamlit as st
import sys
import os

# --- PATH SETUP ---
# Get the root directory (parent of 'pages')
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
app_dir = os.path.join(root_dir, "Real_estate")

# Add to sys.path to allow imports
if app_dir not in sys.path:
    sys.path.append(app_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# --- CONFIG ---
# Set page config for the wrapper
st.set_page_config(page_title="Парсер Реєстру Нерухомості", page_icon="🏠", layout="wide")

from utils import remove_max_width
remove_max_width()

# --- IMPORT & RUN ---
# The Real Estate module has all code at top level, so we need to exec it
# instead of importing normally (which would run st.set_page_config twice)
try:
    main_file_path = os.path.join(app_dir, "main.py")

    # Read the main.py file content
    with open(main_file_path, 'r', encoding='utf-8') as f:
        main_code = f.read()

    # Remove the st.set_page_config line to avoid duplicate config error
    import re
    import pdfplumber
    import warnings
    import logging
    from io import BytesIO

    main_code = re.sub(r"st\.set_page_config\([^)]+\)", "# st.set_page_config removed by wrapper", main_code)

    # Execute the modified code in the current namespace with all required imports
    exec_globals = {
        '__name__': '__main__',
        'st': st,
        'os': os,
        'sys': sys,
        're': re,
        'pdfplumber': pdfplumber,
        'warnings': warnings,
        'logging': logging,
        'BytesIO': BytesIO
    }
    exec(main_code, exec_globals)

except Exception as e:
    st.error(f"Помилка при запуску додатку Real Estate: {e}")
    # Print stack trace for debugging
    import traceback
    st.code(traceback.format_exc())
    st.info(f"App dir: {app_dir}")
