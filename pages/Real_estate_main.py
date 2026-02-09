import streamlit as st
from io import BytesIO
from real_estate_processor import parse_real_estate_pdf, append_real_estate_to_doc
from docx import Document
import base64


def get_binary_file_downloader_html(bin_file, file_label='File'):
    """
    Generates a link allowing the data in a given binary file to be downloaded
    """
    bin_str = base64.b64encode(bin_file).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}">📥 Завантажити {file_label}</a>'
    return href


def main():
    st.set_page_config(
        page_title="Нерухомість",
        page_icon="🏢",
        layout="wide"
    )

    st.title("🏢 Обробка нерухомості")
    st.markdown("---")

    # Завантаження файлів
    st.header("Завантаження PDF файлів нерухомості")
    
    uploaded_files = st.file_uploader(
        "Виберіть PDF файли для обробки",
        type=['pdf'],
        accept_multiple_files=True,
        help="Можна завантажити кілька файлів одночасно"
    )

    if uploaded_files:
        st.success(f"✅ Завантажено файлів: {len(uploaded_files)}")

        # Показуємо список завантажених файлів
        with st.expander("📋 Список завантажених файлів"):
            for i, file in enumerate(uploaded_files, 1):
                st.write(f"{i}. {file.name} ({file.size / 1024:.2f} KB)")

        if st.button("🔄 Обробити файли нерухомості", type="primary"):
            with st.spinner("Обробка файлів нерухомості..."):
                all_real_estate_data = []
                
                for uploaded_file in uploaded_files:
                    # Seek to the beginning of the file
                    uploaded_file.seek(0)
                    
                    real_estate_data, error = parse_real_estate_pdf(uploaded_file)
                    
                    if error:
                        st.error(f"Помилка обробки файлу {uploaded_file.name}: {error}")
                    else:
                        if real_estate_data:
                            all_real_estate_data.extend(real_estate_data)
                            st.success(f"✅ Оброблено файл: {uploaded_file.name}")
                
                if all_real_estate_data:
                    st.session_state['real_estate_data'] = all_real_estate_data
                    st.success(f"✅ Успішно оброблено {len(uploaded_files)} файлів. Знайдено {len(all_real_estate_data)} записів нерухомості.")
                else:
                    st.warning("Не знайдено даних про нерухомість у завантажених файлах.")

    # Генерація DOCX
    if 'real_estate_data' in st.session_state and st.session_state['real_estate_data']:
        st.markdown("---")
        st.header("Генерація DOCX з результатами")
        
        if st.button("📥 Згенерувати DOCX", type="primary"):
            with st.spinner("Створення документа..."):
                # Створюємо новий документ
                doc = Document()
                
                # Додаємо інформацію про нерухомість
                append_real_estate_to_doc(doc, st.session_state['real_estate_data'])
                
                # Зберігаємо документ у буфер
                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                
                # Пропонуємо завантажити
                st.markdown(get_binary_file_downloader_html(buffer.getvalue(), 'nerukhomist.docx'), unsafe_allow_html=True)


if __name__ == "__main__":
    main()