import streamlit as st
import json
import os

try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.getcwd() != script_dir:
        os.chdir(script_dir)
except Exception as e:
    st.error(f"Failed to reset CWD: {e}")

st.set_page_config(
    page_title="Корпоративний Портал Додатків",
    page_icon="</>",
    layout="wide"
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background-color: #0d1117;
    }
    
    .stMainBlockContainer {
        max-width: none;
        padding: 2rem 3rem;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .portal-header {
        text-align: center;
        padding: 3rem 0 2rem 0;
        margin-bottom: 2rem;
        border-bottom: 1px solid #30363d;
    }
    
    .portal-title {
        font-family: 'Inter', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #58a6ff 0%, #a371f7 50%, #f78166 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    .portal-subtitle {
        font-family: 'JetBrains Mono', monospace;
        color: #8b949e;
        font-size: 1rem;
        margin-top: 1rem;
    }
    
    .code-decor {
        font-family: 'JetBrains Mono', monospace;
        color: #30363d;
        font-size: 1.2rem;
        margin: 0 0.5rem;
    }
    
    .stats-bar {
        display: flex;
        justify-content: center;
        gap: 3rem;
        margin-top: 1.5rem;
        flex-wrap: wrap;
    }
    
    .stat-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
    }
    
    .stat-value {
        color: #58a6ff;
        font-weight: 600;
    }
    
    .stat-label {
        color: #8b949e;
    }
    
    .portal-footer {
        text-align: center;
        padding: 2rem 0;
        margin-top: 2rem;
        border-top: 1px solid #30363d;
    }
    
    .footer-text {
        font-family: 'JetBrains Mono', monospace;
        color: #484f58;
        font-size: 0.8rem;
    }
    
    .footer-link {
        color: #58a6ff;
        text-decoration: none;
    }
    
    div[data-testid="stHorizontalBlock"] {
        gap: 20px !important;
    }
    
    div[data-testid="stHorizontalBlock"] > div > div > div {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    
    .card-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        flex-shrink: 0;
    }
    
    .icon-gradient-1 { background: linear-gradient(135deg, #58a6ff 0%, #388bfd 100%); }
    .icon-gradient-2 { background: linear-gradient(135deg, #238636 0%, #2ea043 100%); }
    .icon-gradient-3 { background: linear-gradient(135deg, #a371f7 0%, #8957e5 100%); }
    .icon-gradient-4 { background: linear-gradient(135deg, #f78166 0%, #da3633 100%); }
    .icon-gradient-5 { background: linear-gradient(135deg, #d29922 0%, #e3b341 100%); }
    .icon-gradient-6 { background: linear-gradient(135deg, #3fb950 0%, #2ea043 100%); }
    .icon-gradient-7 { background: linear-gradient(135deg, #f778ba 0%, #db61a2 100%); }
    
    .app-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.5rem;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
        min-height: 200px;
        display: flex;
        flex-direction: column;
    }
    
    .app-card:hover {
        border-color: #58a6ff;
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(88, 166, 255, 0.15);
    }
    
    .app-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #58a6ff, #a371f7);
        opacity: 0;
        transition: opacity 0.2s ease;
    }
    
    .app-card:hover::before {
        opacity: 1;
    }
    
    .card-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    
    .card-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: #c9d1d9;
        margin: 0;
    }
    
    .card-description {
        color: #8b949e;
        font-size: 0.9rem;
        line-height: 1.5;
        flex-grow: 1;
    }
    
    .app-card-footer {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #30363d;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #58a6ff;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
    }
    
    .app-card-error {
        border-color: #f85149 !important;
    }
    
    .app-card-error .app-card-footer {
        color: #f85149 !important;
    }
    
    .stButton {
        margin-top: auto;
    }
    
    .stButton button {
        width: 100% !important;
        background: rgba(88, 166, 255, 0.1) !important;
        border: 1px solid transparent !important;
        border-radius: 6px !important;
        color: #58a6ff !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton button:hover {
        background: rgba(88, 166, 255, 0.2) !important;
        border-color: #58a6ff !important;
    }
    
    .card-error button {
        background: rgba(248, 81, 73, 0.1) !important;
        color: #f85149 !important;
    }
    
    .card-error button:hover {
        background: rgba(248, 81, 73, 0.2) !important;
        border-color: #f85149 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def load_apps_config():
    config_path = os.path.join(script_dir, "apps_config.json")
    if not os.path.exists(config_path):
        st.error(f"Файл конфігурації {config_path} не знайдено.")
        return []
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_icon_gradient(index):
    gradients = [
        "icon-gradient-1",
        "icon-gradient-2", 
        "icon-gradient-3",
        "icon-gradient-4",
        "icon-gradient-5",
        "icon-gradient-6",
        "icon-gradient-7",
    ]
    return gradients[index % len(gradients)]

def render_app_card(app, index):
    icon = app.get('icon', '📱')
    name = app['name']
    description = app['description']
    page_path = app['page_file']
    gradient_class = get_icon_gradient(index)
    
    file_exists = os.path.exists(page_path)
    error_class = "" if file_exists else "app-card-error"
    
    card_header_html = f'''
    <div class="app-card {error_class}">
        <div class="card-header">
            <div class="card-icon {gradient_class}">{icon}</div>
            <h3 class="card-title">{name}</h3>
        </div>
        <p class="card-description">{description}</p>
    '''
    st.markdown(card_header_html, unsafe_allow_html=True)
    
    if file_exists:
        if st.button("Відкрити →", key=f"btn_{index}", use_container_width=True):
            st.switch_page(page_path)
    else:
        st.markdown('<div class="app-card-footer"><span>Файл не знайдено</span></div></div>', unsafe_allow_html=True)

def main():
    apps = load_apps_config()
    
    header_html = f"""
    <div class="portal-header">
        <h1 class="portal-title">
            <span class="code-decor">&lt;/&gt;</span>
            Корпоративний Портал
            <span class="code-decor">&#123; &#125;</span>
        </h1>
        <p class="portal-subtitle">// Інструменти для аналітики та обробки даних</p>
        <div class="stats-bar">
            <div class="stat-item">
                <span class="stat-value">{len(apps)}</span>
                <span class="stat-label">додатків</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">v2.0</span>
                <span class="stat-label">версія</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">24/7</span>
                <span class="stat-label">доступність</span>
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
    
    if not apps:
        st.warning("Немає доступних додатків у конфігурації.")
        return
    
    cols = st.columns(3)
    for idx, app in enumerate(apps):
        with cols[idx % 3]:
            render_app_card(app, idx)
    
    footer_html = """
    <div class="portal-footer">
        <p class="footer-text">
            <span class="code-decor">&lt;/&gt;</span>
            Корпоративний Портал Додатків © 2025
            <span class="code-decor">|</span>
            Powered by <span class="footer-link">Streamlit</span>
        </p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()