import streamlit as st
import json
import os

# --- FORCE CWD TO SCRIPT DIRECTORY ---
# This ensures that even if sub-apps change CWD, Home.py restores it.
# This fixes the "File not found" errors for relative paths like "pages/..."
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.getcwd() != script_dir:
        os.chdir(script_dir)
except Exception as e:
    st.error(f"Failed to reset CWD: {e}")

st.set_page_config(
    page_title="Корпоративний Портал Додатків",
    page_icon="🏢",
    layout="wide"
)

# Прибираємо max-width для stMainBlockContainer
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

def load_apps_config():
    # Now that CWD is forced, simple path should work, but absolute is still safer for reading
    config_path = os.path.join(script_dir, "apps_config.json")

    if not os.path.exists(config_path):
        st.error(f"Файл конфігурації {config_path} не знайдено. CWD: {os.getcwd()}")
        return []
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    st.title("🏢 Корпоративний Портал Додатків")
    st.markdown("---")

    apps = load_apps_config()

    if not apps:
        st.warning("Немає доступних додатків у конфігурації.")
        return

    # Use columns to display apps in a grid
    cols = st.columns(3)

    for idx, app in enumerate(apps):
        with cols[idx % 3]:
            st.info(f"### {app.get('icon', '📱')} {app['name']}")
            st.write(app['description'])

            # Streamlit page links work best in sidebar, but for buttons we can use page_link if on newer streamlit
            # Or just instruct user to use sidebar.
            # Using st.page_link (Requires Streamlit 1.31+)
            page_path = app['page_file']
            if os.path.exists(page_path):
                st.page_link(page_path, label="Відкрити", icon="🚀")
            else:
                st.warning(f"Файл {page_path} не знайдено")


if __name__ == "__main__":
    main()
