import streamlit as st
import os
import base64

st.set_page_config(page_title="BM DOCX Viewer", page_icon="📄", layout="wide")

from utils import remove_max_width
remove_max_width()

def get_base64_image(image_path):
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def main():
    st.title("📄 Обробка архивів з БМ")

    # Define paths
    current_dir = os.path.dirname(os.path.abspath(__file__)) # pages/
    root_dir = os.path.dirname(current_dir)
    bm_dir = os.path.join(root_dir, "BM_v_DOCX")
    html_path = os.path.join(bm_dir, "index.html")

    if not os.path.exists(html_path):
        st.error(f"HTML файл не знайдено: {html_path}")
        return

    # Read HTML
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Handle Images (specifically the logo mentioned in code analysis)
    # <img src="./images/photo_2025-09-22_22-10-14-Photoroom.png"
    img_rel_path = "images/photo_2025-09-22_22-10-14-Photoroom.png"
    img_abs_path = os.path.join(bm_dir, img_rel_path)

    b64_img = get_base64_image(img_abs_path)
    if b64_img:
        # Determine mime type (png based on filename)
        mime = "image/png"
        src_replacement = f"data:{mime};base64,{b64_img}"
        # Replace relative path with base64
        html_content = html_content.replace("./" + img_rel_path, src_replacement)
        html_content = html_content.replace(img_rel_path, src_replacement) # Try both with and without ./

    # Render
    # Using a high height to accommodate the tool
    st.components.v1.html(html_content, height=1000, scrolling=True)

if __name__ == "__main__":
    main()
