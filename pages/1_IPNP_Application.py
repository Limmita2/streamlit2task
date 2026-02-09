import streamlit as st
import sys
import os

# --- PATH SETUP ---
# Get the root directory (parent of 'pages')
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
app_dir = os.path.join(root_dir, "IPNP_v_HTML")

# Add to sys.path to allow imports
if app_dir not in sys.path:
    sys.path.append(app_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# --- CONFIG ---
# Set config HERE because we removed it from the global scope of the imported app
st.set_page_config(page_title="IPNP Application", page_icon="📝", layout="wide")

from utils import remove_max_width
remove_max_width()

# --- IMPORT & RUN ---
try:
    import IPNP_v_HTML.app as ipnp_app

    # Run the main function if it exists
    if hasattr(ipnp_app, 'main'):
        ipnp_app.main()
    else:
        st.error("В модулі IPNP_v_HTML.app не знайдено функцію main().")

except Exception as e:
    st.error(f"Помилка при запуску додатку IPNP: {e}")
    # Print stack trace for debugging
    import traceback
    st.code(traceback.format_exc())
    st.info(f"App dir: {app_dir}")
