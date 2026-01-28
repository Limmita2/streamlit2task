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