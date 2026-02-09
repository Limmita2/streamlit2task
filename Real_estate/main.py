import streamlit as st
import pdfplumber
import re
import warnings
import logging
from io import BytesIO

# --- НАСТРОЙКИ ЛОГИРОВАНИЯ (Чистая консоль) ---
logging.getLogger("pdfminer").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(page_title="Парсер Реєстру Нерухомості", layout="wide")

# --- CSS СТИЛИ ---
st.markdown("""
<style>
    .reportview-container {
        font-family: 'Times New Roman', Times, serif;
    }
    .result-container {
        font-family: 'Times New Roman', Times, serif;
        font-size: 19px; 
        line-height: 1.6;
        background-color: #f5f5f5;
        border: 1px solid #cccccc;
        border-radius: 5px;
        padding: 20px;
        color: #000000;
        /* white-space: pre-wrap; УБРАНО, так как используем <br> для переносов */
    }
    .result-container strong {
        font-weight: bold;
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)

# --- ФУНКЦИИ ПАРСИНГА ---

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def extract_field(text, field_name, stop_at=None):
    base_pattern = re.escape(field_name) + r'\s*:\s*'
    if stop_at:
        stop_pattern = r'(.*?)(?=' + re.escape(stop_at) + r'|\Z)'
    else:
        stop_pattern = r'(.*?)(?=\s+[А-ЯІЇЄ][А-ЯІЇЄа-яіїє’\s]+:|ВІДОМОСТІ|Актуальна|Дата|\Z)'
    
    full_pattern = base_pattern + stop_pattern
    match = re.search(full_pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return clean_text(match.group(1))
    return None

def parse_pdf_file(uploaded_file):
    try:
        full_text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        
        full_text = clean_text(full_text)
        results = []

        if not full_text:
            return "Не удалось прочитать текст из файла."

        blocks = full_text.split("З ДЕРЖАВНОГО РЕЄСТРУ РЕЧОВИХ ПРАВ")

        for block in blocks:
            if not block or len(block) < 50:
                continue

            # --- Блок "ВІДОМОСТІ ПРО ОБ’ЄКТ НЕРУХОМОГО МАЙНА" ---
            legacy_pattern = r"ВІДОМОСТІ ПРО ОБ’ЄКТ НЕРУХОМОГО МАЙНА"
            legacy_match = re.search(legacy_pattern, block)

            if legacy_match:
                legacy_start = legacy_match.end()
                next_header_match = re.search(r"ВІДОМОСТІ ПРО ПРАВА|ВІДОМОСТІ З ЄДИНОГО", block[legacy_start:])
                legacy_end = len(block) if not next_header_match else legacy_start + next_header_match.start()
                legacy_text = block[legacy_start:legacy_end]
                
                p_type = extract_field(legacy_text, "Тип майна", stop_at="Адреса нерухомого майна:")
                p_address = extract_field(legacy_text, "Адреса нерухомого майна", stop_at="Загальна площа (кв.м):")
                p_area = extract_field(legacy_text, "Загальна площа (кв.м)", stop_at="Номер запису:")
                
                if p_type or p_address or p_area:
                    results.append({
                        "Тип майна": p_type,
                        "Адреса нерухомого майна": p_address,
                        "Загальна площа (кв.м)": p_area
                    })

            # --- Блок Обременений ---
            enc_pattern = r"Актуальна інформація про державну реєстрацію обтяжень"
            enc_match = re.search(enc_pattern, block)

            if enc_match:
                enc_start = enc_match.end()
                next_section_match = re.search(r"(Актуальна інформація про об’єкт|ВІДОМОСТІ З РЕЄСТРУ)", block[enc_start:])
                
                enc_end = len(block)
                if next_section_match:
                    enc_end = enc_start + next_section_match.start()
                
                enc_text = block[enc_start:enc_end]
                
                enc_basis = extract_field(enc_text, "Підстава внесення запису", stop_at="Вид обтяження:")
                enc_type = extract_field(enc_text, "Вид обтяження")
                
                if enc_type or enc_basis:
                    results.append({
                        "Вид обтяження": enc_type,
                        "Підстава внесення запису": enc_basis
                    })

            # --- Основные объекты ---
            section_a_pattern = r"Актуальна інформація про об’єкт речових прав"
            section_b_pattern = r"Актуальна інформація про речове право"

            a_matches = list(re.finditer(section_a_pattern, block))
            b_matches = list(re.finditer(section_b_pattern, block))

            for i, a_match in enumerate(a_matches):
                current_a_start = a_match.end()
                next_a_match = a_matches[i+1] if (i + 1) < len(a_matches) else None
                
                relevant_b_match = None
                for b_match in b_matches:
                    if b_match.start() > a_match.start():
                        relevant_b_match = b_match
                        break
                
                section_a_end = len(block)
                if relevant_b_match:
                    section_a_end = relevant_b_match.start()
                elif next_a_match:
                    section_a_end = next_a_match.start()
                
                section_a_text = block[current_a_start:section_a_end]

                if "Реєстраційний номер об’єкта" not in section_a_text:
                    continue

                obj_type = extract_field(section_a_text, "Тип об’єкта")
                if not obj_type:
                    continue

                obj_data = {}

                if "земельна" in obj_type.lower():
                    cad_num = extract_field(section_a_text, "Кадастровий номер")
                    obj_desc = extract_field(section_a_text, "Опис об’єкта")
                    obj_data = {
                        "Тип об’єкта": obj_type,
                        "Кадастровий номер": cad_num,
                        "Опис об’єкта": obj_desc
                    }
                    
                    if relevant_b_match:
                        b_start = relevant_b_match.end()
                        b_end = len(block)
                        if next_a_match:
                            b_end = next_a_match.start()
                        section_b_text = block[b_start:b_end]
                        
                        # Ищем "Розмір частки:" и "Дата, час державної реєстрації:" в том же разделе
                        share = extract_field(section_b_text, "Розмір частки")
                        if share and share != "1/1":
                            obj_data["Розмір частки"] = share
                        
                        # Ищем "Дата, час державної реєстрації:" в том же разделе
                        registration_date = extract_field(section_b_text, "Дата, час державної реєстрації")
                        if registration_date:
                            obj_data["Дата, час державної реєстрації"] = registration_date
                else:
                    address = extract_field(section_a_text, "Адреса")
                    obj_desc = extract_field(section_a_text, "Опис об’єкта")
                    obj_data = {
                        "Тип об’єкта": obj_type,
                        "Опис об’єкта": obj_desc,
                        "Адреса": address
                    }

                    if relevant_b_match:
                        b_start = relevant_b_match.end()
                        b_end = len(block)
                        if next_a_match:
                            b_end = next_a_match.start()
                        section_b_text = block[b_start:b_end]
                        share = extract_field(section_b_text, "Розмір частки")
                        if share and share != "1/1":
                            obj_data["Розмір частки"] = share
                        
                        # Ищем "Дата, час державної реєстрації:" в том же разделе
                        registration_date = extract_field(section_b_text, "Дата, час державної реєстрації")
                        if registration_date:
                            obj_data["Дата, час державної реєстрації"] = registration_date

                if obj_data:
                    results.append(obj_data)

        if not results:
            return "Немає зареєстрованої нерухомості"

        return results

    except Exception as e:
        return f"Помилка обробки файлу: {str(e)}"

def format_output(all_data):
    output_lines = []
    
    # enumerate дает сквозную нумерацию
    for i, item in enumerate(all_data, 1):
        if isinstance(item, str):
            output_lines.append(item)
        else:
            for key, value in item.items():
                if value:
                    output_lines.append(f"{key}: {value}")
        
        # Два пустых элемента списка создадут два <br> (двойной отступ)
        output_lines.append("") 
            
    # Соединяем через <br> вместо \n для корректного рендеринга HTML в Streamlit
    return "<br>".join(output_lines)

# --- ИНТЕРФЕЙС STREAMLIT ---

st.title("📄 Парсер виписок з Реєстру Нерухомості")
st.write("Завантажте один або кілька PDF-файлів для обробки.")

uploaded_files = st.file_uploader(
    "Виберіть PDF файли", 
    type="pdf", 
    accept_multiple_files=True
)

if st.button("Обробити файли"):
    if not uploaded_files:
        st.warning("Будь ласка, завантажте хоча б один файл.")
    else:
        global_results = []
        progress_bar = st.progress(0)
        
        for idx, file in enumerate(uploaded_files):
            result = parse_pdf_file(file)
            
            if isinstance(result, list):
                global_results.extend(result)
            else:
                global_results.append(result)
            
            progress_bar.progress((idx + 1) / len(uploaded_files))
        
        if not global_results:
            formatted_text = "Немає даних для відображення."
        else:
            formatted_text = format_output(global_results)
        
        st.markdown("### Результат:")
        st.markdown(f'<div class="result-container">{formatted_text}</div>', unsafe_allow_html=True)
        
        # Для скачивания используем обычные переносы строк
        download_text = formatted_text.replace("<br>", "\n").replace("**", "")
        st.download_button(
            label="Завантажити результат як .txt",
            data=download_text,
            file_name="result.txt",
            mime="text/plain"
        )