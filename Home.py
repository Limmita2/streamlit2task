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

def load_apps_config():
    # Now that CWD is forced, simple path should work, but absolute is still safer for reading
    config_path = os.path.join(script_dir, "apps_config.json")
    
    if not os.path.exists(config_path):
        st.error(f"Файл конфигурации {config_path} не найден. CWD: {os.getcwd()}")
        return []
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    st.title("🏢 Корпоративний Портал Додатків")
    st.markdown("---")

    apps = load_apps_config()

    if not apps:
        st.warning("Нет доступных приложений в конфигурации.")
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
                 st.page_link(page_path, label="Открыть", icon="🚀")
            else:
                st.warning(f"Файл {page_path} не найден")

    st.markdown("---")
    st.markdown("---")
    with st.expander("➕ Добавить новое приложение"):
        with st.form("add_app_form"):
            new_name = st.text_input("Название приложения")
            new_desc = st.text_area("Описание")
            new_icon = st.text_input("Иконка (emoji)", value="📱")
            new_file = st.text_input("Путь к файлу (например: pages/MyApp.py)")
            password = st.text_input("Пароль администратора", type="password")
            
            submitted = st.form_submit_button("Добавить")
            if submitted:
                if password != "ke050442":
                    st.error("Неверный пароль администратора!")
                    st.stop()
                
                if new_name and new_file:
                    new_app = {
                        "name": new_name,
                        "description": new_desc,
                        "page_file": new_file,
                        "icon": new_icon
                    }
                    apps.append(new_app)
                    try:
                        # Use absolute path to save apps_config.json
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        config_path = os.path.join(current_dir, "apps_config.json")
                        
                        with open(config_path, "w", encoding="utf-8") as f:
                            json.dump(apps, f, ensure_ascii=False, indent=4)
                        st.success("Приложение добавлено! Обновите страницу.")
                    except Exception as e:
                        st.error(f"Ошибка сохранения: {e}")
                else:
                    st.error("Название и путь к файлу обязательны.")

if __name__ == "__main__":
    main()
