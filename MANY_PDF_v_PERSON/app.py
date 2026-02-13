import streamlit as st
import os
import io
import base64
import time
import re
from io import BytesIO
from pdf_processor import process_pdfs_to_paragraphs
from document_generator import generate_docx
from docx_to_pdf_converter import convert_docx_to_pdf, get_pdf_filename_from_docx
from direct_pdf_creator import create_pdf_directly, get_pdf_filename_from_intro
from PIL import Image
from streamlit_sortables import sort_items
from streamlit_pdf_viewer import pdf_viewer
from arkan_processor import process_excel_to_data
import dms_processor
from dms_processor import extract_dms_data
from real_estate_processor import parse_real_estate_pdf
from car_processor import append_car_to_doc
import pandas as pd


# --- ФУНКЦІЇ ДЛЯ ОБРОБКИ ДАНИХ ПРО ТЗ ---

def parse_vehicle_data(text):
    """Парсить текст та витягує дані про ТЗ"""
    result = {}

    # Шаблони для пошуку
    patterns = {
        'номерний_знак': [
            r'Державний номер[:\s]*([A-ZА-ЯІЇЄҐ0-9]+)',
            r'Номерний знак[:\s]*([A-ZА-ЯІЇЄҐ0-9]+)',
            r'НОМЕРНИЙ ЗНАК[:\s]*([A-ZА-ЯІЇЄҐ0-9]+)',
        ],
        'власник': [
            r'Власник[:\s]*([A-ZА-ЯІЇЄҐ\s]+?)(?=\s*\d{2}\.\d{2}\.\d{4}|\s*$)',
        ],
        'дата_народження': [
            r'Дата народження[:\s]*(\d{2}\.\d{2}\.\d{4})',
            r'Власник[:\s]*[A-ZА-ЯІЇЄҐ\s]+(\d{2}\.\d{2}\.\d{4})',
        ],
        'іпн': [
            r'ІПН[:\s]*(\d+)',
            r'ІПН/ЄДРПОУ[:\s]*(\d+)',
        ],
        'місце_реєстрації': [
            r'Адреса власника[:\s]*([^\n]+)',
            r'Адреса реєстрації ТЗ[:\s]*([^\n]+)',
        ],
        'марка': [
            r'Марка/модель ТЗ[:\s]*([A-Z]+)',
        ],
        'модель': [
            r'Марка/модель ТЗ[:\s]*[A-Z]+\s+([A-Z0-9]+(?:\s+[A-Z0-9.]+)?)',
        ],
        'vin': [
            r'vin ТЗ[:\s]*([A-Z0-9]+)',
            r'VIN[:\s]*([A-Z0-9]+)',
        ],
        'колір': [
            r'Колір ТЗ[:\s]*([A-ZА-ЯІЇЄҐ]+)',
            r'Колір[:\s]*([A-ZА-ЯІЇЄҐ]+)',
        ],
        'рік_випуску': [
            r'Рік випуску[:\s]*(\d{4})',
            r'Рік випуску[:\s]*([0-9]{4})',
            r'Рік[:\s]*випуску[:\s]*(\d{4})',
            r'(\d{4})\s*рік випуску',
            r'рік випуску.*?(\d{4})',
            r'(\d{4})\s*р.',
            r'(\d{4})\s*року',
        ],
    }

    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result[field] = match.group(1).strip()
                break

    # Спеціальна обробка для марка/модель з тексту
    if 'марка' not in result:
        match = re.search(r'Марка/модель ТЗ[:\s]*([^\n]+)', text, re.IGNORECASE)
        if match:
            full = match.group(1).strip()
            parts = full.split()
            if len(parts) >= 1:
                result['марка'] = parts[0]
            if len(parts) >= 2:
                result['модель'] = ' '.join(parts[1:])

    return result


def parse_excel_file(df):
    """Парсить Excel файл специфічного формату"""
    result = {}

    # Перетворюємо DataFrame у словник для пошуку
    text = df.to_string()

    # Проходимо по всіх клітинках
    for idx, row in df.iterrows():
        for col_idx, cell in enumerate(row):
            if pd.notna(cell):
                cell_str = str(cell).strip()

                # Номерний знак
                if 'НОМЕРНИЙ ЗНАК' in cell_str.upper():
                    # Значення в наступній колонці
                    if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                        result['номерний_знак'] = str(row.iloc[col_idx + 1]).strip()

                # Власник
                if 'Власник' in cell_str and ':' in cell_str:
                    match = re.search(r'Власник[:\s]*([A-ZА-ЯІЇЄҐ\s]+)', cell_str)
                    if match:
                        result['власник'] = match.group(1).strip()

                # Дата народження
                if 'Дата народження' in cell_str:
                    match = re.search(r'(\d{2}\.\d{2}\.\d{4})', cell_str)
                    if match:
                        result['дата_народження'] = match.group(1)

                # ІПН
                if 'ІПН' in cell_str:
                    # Шукаємо в тій самій клітинці
                    match = re.search(r'ІПН[:\s]*(\d+)', cell_str)
                    if match:
                        result['іпн'] = match.group(1)
                    # Або в наступній клітинці
                    elif col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                        val = str(row.iloc[col_idx + 1]).strip()
                        if val.isdigit():
                            result['іпн'] = val

                # Місце реєстрації
                if 'Місце реєстрації' in cell_str:
                    match = re.search(r'Місце реєстрації[:\s]*(.+)', cell_str)
                    if match:
                        result['місце_реєстрації'] = match.group(1).strip()

                # Марка
                if cell_str.strip() == 'Марка':
                    # Значення в наступній колонці
                    if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                        result['марка'] = str(row.iloc[col_idx + 1]).strip()

                # Модель
                if cell_str.strip() == 'Модель':
                    if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                        result['модель'] = str(row.iloc[col_idx + 1]).strip()

                # VIN
                if cell_str.strip() == 'VIN':
                    if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                        result['vin'] = str(row.iloc[col_idx + 1]).strip()

                # Колір
                if cell_str.strip() == 'Колір':
                    if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                        result['колір'] = str(row.iloc[col_idx + 1]).strip()

                # Рік випуску
                if cell_str.strip() == 'Рік випуску':
                    if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                        result['рік_випуску'] = str(row.iloc[col_idx + 1]).strip()
                elif 'Рік випуску' in cell_str:
                    match = re.search(r'(\d{4})', cell_str)
                    if match:
                        result['рік_випуску'] = match.group(1)

    # Якщо не знайшли через структуру, шукаємо через текст
    if not result:
        result = parse_vehicle_data(text)

    # Дозаповнюємо пропущені поля з тексту
    text_result = parse_vehicle_data(text)
    for key, value in text_result.items():
        if key not in result or not result[key]:
            result[key] = value

    return result


# Налаштування сторінки
# Налаштування сторінки
# st.set_page_config(
#     page_title="Генератор досьє з PDF",
#     page_icon="📄",
#     layout="wide"
# )

# Стилі CSS для покращення інтерфейсу
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #0051a8;
        color: white;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border: none;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #003d7a;
    }
    .upload-section {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    h1 {
        color: #0051a8;
        font-weight: bold;
    }
    h2 {
        color: #003d7a;
        margin-top: 2rem;
    }
    h3 {
        color: #0051a8;
        margin-top: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)


def cleanup_temp_photos(exclude_path=None):
    """Видаляє всі тимчасові фото, крім поточного активного."""
    for f in os.listdir("."):
        if f.startswith("temp_photo_") and f.endswith(".png"):
            try:
                full_path = os.path.abspath(f)
                if exclude_path and os.path.abspath(exclude_path) == full_path:
                    continue
                os.remove(f)
            except:
                pass


def main():
    # Очищення старих фото більше не потрібно, оскільки фото зберігаються в session_state

    # Заголовок
    st.title("📄 Генератор особистого досьє з PDF")
    st.markdown("---")

    # Основна область
    # Секція завантаження файлів
    st.header("1️⃣ Завантаження PDF файлів")

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

        # Кнопка обробки
        if st.button("🔄 Обробити PDF файли", type="primary"):
            with st.spinner("Обробка PDF файлів..."):
                all_paragraphs = process_pdfs_to_paragraphs(uploaded_files)

                # Зберігаємо в session_state
                st.session_state['all_paragraphs'] = all_paragraphs
                st.session_state['processing_done'] = True
                # Скидаємо вибір при новій обробці
                if 'selections' in st.session_state:
                    del st.session_state['selections']

                st.success("✅ Обробка завершена!")

    # Секция 2: Выбор и Секция 3: Фото
    if 'processing_done' in st.session_state and st.session_state['processing_done']:
        st.markdown("---")
        st.header("2️⃣ Вибір інформації з файлів")

        all_paragraphs_dict = st.session_state['all_paragraphs']

        if 'selections' not in st.session_state:
            st.session_state['selections'] = {}

        selected_content = []

        # --- Разделенный экран: Текст (слева) и PDF (справа) ---
        file_names = list(all_paragraphs_dict.keys())
        active_file = file_names[0]
        if len(file_names) > 1:
            active_file = st.radio("📂 Оберіть файл для перегляду:", file_names, horizontal=True)

        paragraphs = all_paragraphs_dict[active_file]
        # Динамічний розрахунок висоти: приблизно 115 пікселів на блок + заголовок
        pdf_height = max(800, len(paragraphs) * 115 + 100)

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown("#### 📝 Вибір блоків")

            if active_file not in st.session_state['selections']:
                st.session_state['selections'][active_file] = [True] * len(paragraphs)

            with st.container():
                for i, block in enumerate(paragraphs):
                    header = block.get("header", "")
                    content = block.get("content", "")
                    key = f"cb_{active_file}_{i}"

                    display_header = f"**{header}**" if header else f"Блок {i+1}"
                    is_selected = st.checkbox(display_header, value=st.session_state['selections'][active_file][i], key=key)

                    if content:
                        st.caption(content)

                    st.session_state['selections'][active_file][i] = is_selected

        with col_right:
            st.markdown("#### 📑 Оригінальний PDF")
            # Знаходимо об'єкт файлу
            file_obj = next((f for f in uploaded_files if f.name == active_file), None)
            if file_obj:
                file_obj.seek(0)
                # Використання спеціалізованої бібліотеки для Streamlit Cloud
                pdf_viewer(file_obj.read(), height=pdf_height)

        # Собираем выбранное
        for fname, f_paras in all_paragraphs_dict.items():
            if fname in st.session_state['selections']:
                for i, sel in enumerate(st.session_state['selections'][fname]):
                    if sel:
                        block = f_paras[i].copy()
                        block['filename'] = fname
                        block['idx'] = i
                        selected_content.append(block)
    else:
        selected_content = []

    # ПЕРЕНЕСЕНО СЮДИ: Секція завантаження фото (завжди доступна після вибору файлів або відразу)
    st.markdown("---")
    st.header("3️⃣ Налаштування фото")

    col1, col2 = st.columns([1, 1])

    with col1:
        if 'last_processed_paste' not in st.session_state:
            st.session_state['last_processed_paste'] = ""

        uploaded_photo = st.file_uploader(
            "Завантажте фото або скопіюйте картинку (Ctrl+V)",
            type=['png', 'jpg', 'jpeg'],
            key="photo_uploader"
        )

        paste_placeholder = "ОЧІКУВАННЯ_ВСТАВКИ_ЗОБРАЖЕННЯ"

        # Ховаємо поле Брідж через CSS
        st.markdown(f"""
            <style>
                div[data-testid="stTextArea"]:has(textarea[placeholder="{paste_placeholder}"]) {{
                    height: 0px !important;
                    min-height: 0px !important;
                    overflow: hidden !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    opacity: 0;
                }}
            </style>
        """, unsafe_allow_html=True)

        paste_result = st.text_area(
            "Bridge",
            key="clipboard_data",
            height=1,
            placeholder=paste_placeholder,
            label_visibility="collapsed"
        )

        # 1. ОБРОБКА ВСТАВКИ (якщо дані нові)
        if paste_result and paste_result != st.session_state['last_processed_paste']:
            try:
                if not paste_result.startswith("data:image"):
                    raise ValueError("Неправильний формат даних зображення")
                img_data = paste_result.split(",")[1]
                img_bytes = base64.b64decode(img_data)
                img = Image.open(BytesIO(img_bytes))

                # Конвертуємо зображення назад у base64 для зберігання в session_state
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()

                st.session_state['photo_data'] = img_base64
                st.session_state['last_processed_paste'] = paste_result
                # st.rerun()  # Убираем rerun, чтобы избежать циклов
            except Exception as e:
                st.error(f"Помилка вставки: {e}")

        # 2. ОБРОБКА ЗАВАНТАЖЕННЯ (якщо файл вибрано)
        if uploaded_photo:
            # Створюємо хеш або використовуємо ім'я для перевірки змін
            file_id = f"{uploaded_photo.name}_{uploaded_photo.size}"
            if st.session_state.get('last_uploaded_id') != file_id:
                img = Image.open(uploaded_photo)

                # Конвертуємо зображення у base64 для зберігання в session_state
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()

                st.session_state['photo_data'] = img_base64
                st.session_state['last_uploaded_id'] = file_id
                # st.rerun()  # Убираем rerun, чтобы избежать циклов

        import streamlit.components.v1 as components

        components.html(f"""
            <div id="p-zone" contenteditable="true"
                 style="border: 4px dashed #0051a8; padding: 40px; border-radius: 15px; text-align: center; background-color: #f8faff; cursor: pointer; height: 120px; outline: none; transition: all 0.3s;"
                 onclick="this.focus(); document.getElementById('s-msg').innerText='⚡ ГОТОВИЙ ДО ВСТАВКИ (Ctrl+V)';"
                 onblur="document.getElementById('s-msg').innerText='КЛАТЦНІТЬ СЮДИ ТА ТИСНІТЬ Ctrl+V';">
                <span style="font-size: 40px;">📸</span><br>
                <b id="s-msg" style="font-size: 18px; color: #0051a8; font-family: sans-serif;">КЛАТЦНІТЬ СЮДИ ТА ТИСНІТЬ Ctrl+V</b><br>
                <span style="color: #666; font-family: sans-serif; font-size: 14px;">щоб вставити картинку</span>
            </div>

            <script>
            const zone = document.getElementById('p-zone');
            const msg = document.getElementById('s-msg');

            zone.addEventListener('paste', (e) => {{
                e.preventDefault();
                e.stopPropagation();

                const items = (e.clipboardData || e.originalEvent.clipboardData).items;
                let found = false;

                for (let i = 0; i < items.length; i++) {{
                    if (items[i].type.indexOf('image') !== -1) {{
                        found = true;
                        msg.innerText = "⏳ ОБРОБКА...";
                        zone.style.backgroundColor = "#fff9c4";

                        const blob = items[i].getAsFile();
                        const reader = new FileReader();
                        reader.onload = (event) => {{
                            try {{
                                const root = window.parent.document;
                                const ta = root.querySelector('textarea[placeholder="{paste_placeholder}"]');

                                if (ta) {{
                                    // ТРЮК ДЛЯ REACT: використовуємо Native Value Setter
                                    // Також додаємо примусове перемикання фокусу для синхронізації
                                    ta.focus();
                                    const nativeValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                                    nativeValueSetter.call(ta, event.target.result);

                                    // Події для Streamlit
                                    ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    ta.dispatchEvent(new Event('change', {{ bubbles: true }}));

                                    // Перекидаємо фокус на будь-яку кнопку, щоб викликати blur на textarea
                                    const btn = root.querySelector('button');
                                    if (btn) btn.focus();
                                    ta.blur();

                                    msg.innerText = "✅ ГОТОВО! ОНОВЛЕННЯ...";
                                    zone.style.backgroundColor = "#d4edda";
                                }} else {{
                                    msg.innerText = "❌ Помилка зв'язку";
                                    zone.style.backgroundColor = "#ffebee";
                                }}
                            }} catch (err) {{
                                msg.innerText = "❌ Помилка доступу";
                                zone.style.backgroundColor = "#ffebee";
                            }}
                        }};
                        reader.readAsDataURL(blob);
                        break;
                    }}
                }}

                if (!found) {{
                    msg.innerText = "🤔 В БУФЕРІ НЕМАЄ КАРТИНКИ";
                    zone.style.backgroundColor = "#ffecb3";
                    setTimeout(() => {{
                        msg.innerText = "КЛАТЦНІТЬ СЮДИ ТА ТИСНІТЬ Ctrl+V";
                        zone.style.backgroundColor = "#f8faff";
                    }}, 2000);
                }}
            }});
            </script>
        """, height=220)

    with col2:
        if 'photo_data' in st.session_state:
            img_bytes = base64.b64decode(st.session_state['photo_data'])
            img = Image.open(BytesIO(img_bytes))
            st.image(img, caption="Фото для досьє", width=150)
        elif os.path.exists('default_avatar.png'):
            st.image('default_avatar.png', caption="Фото за замовчуванням", width=150)

    # Повертаємо логіку Секції 5 (якщо є вибраний контент)
    if 'processing_done' in st.session_state and st.session_state['processing_done']:

        # Секция сортування
        if selected_content:
            st.markdown("---")
            st.header("5️⃣ Збірка та порядок досьє")
            st.info("💡 1. Перетягніть блоки для зміни порядку. 2. Відредагуйте текст прямо в полях нижче. 3. Натисніть ✖️ для видалення блоку.")

            if 'edited_texts' not in st.session_state:
                st.session_state['edited_texts'] = {}

            # CSS для темно-зеленого тексту на білому фоні в полях редагування
            st.markdown("""
                <style>
                div[data-baseweb="textarea"] textarea {
                    color: #006400 !important;
                    font-weight: 500;
                    background-color: #ffffff !important;
                }
                </style>
            """, unsafe_allow_html=True)

            # 1. Сортування (показуємо компактні "ручки" для перетягування)
            # Сортуємо елементи за заданим порядком: "Початок документа", "Адреса", потім за алфавітом
            sorted_selected_content = []

            # Спочатку додаємо "Початок документа", якщо він є
            for i, item in enumerate(selected_content):
                if item.get('header') == "Початок документа":
                    sorted_selected_content.append(selected_content[i])

            # Потім додаємо "Адреса", якщо вона є
            for i, item in enumerate(selected_content):
                if item.get('header') == "Адреса":
                    sorted_selected_content.append(selected_content[i])

            # Потім додаємо "АВТО (НАІС ТЗ)", якщо воно є
            for i, item in enumerate(selected_content):
                header = item.get('header', '').strip().lower()
                if header in ["авто наіс тз", "авто (наіс тз)", "база наіс тз"]:
                    sorted_selected_content.append(selected_content[i])

            # Потім додаємо інші елементи за алфавітом
            other_items = []
            for item in selected_content:
                header = item.get('header', '').strip().lower()
                if header not in ["початок документа", "адреса"] and header not in ["авто наіс тз", "авто (наіс тз)", "база наіс тз"]:
                    other_items.append(item)

            # Сортуємо інші елементи за заголовком
            other_items.sort(key=lambda x: x.get('header', '').lower())
            sorted_selected_content.extend(other_items)

            # Додаємо можливість видалення блоків
            if 'deleted_blocks' not in st.session_state:
                st.session_state['deleted_blocks'] = set()

            # Відображаємо кожен блок з хрестиком для видалення
            for i, item in enumerate(sorted_selected_content):
                if i not in st.session_state['deleted_blocks']:
                    col1, col2 = st.columns([10, 1])
                    with col1:
                        # Показуємо інформацію про блок
                        block_info = f"[ID:{i}] "
                        if item.get('header'):
                            block_info += f"【{item['header']}】 "
                        content_preview = item.get('content', '')[:50] + "..."
                        st.write(block_info + content_preview)
                    with col2:
                        # Кнопка видалення
                        if st.button("✖️", key=f"delete_{i}", help="Видалити цей блок"):
                            st.session_state['deleted_blocks'].add(i)
                            st.rerun()

            # Створюємо список для сортування з урахуванням видалених блоків
            # Створюємо список елементів, що залишилися, з індексами
            remaining_items = []
            for i, item in enumerate(sorted_selected_content):
                if i not in st.session_state['deleted_blocks']:
                    display_label = f"[ID:{i}] "
                    if item.get('header'):
                        display_label += f"【{item['header']}】 "
                    content_preview = item.get('content', '')[:50] + "..."
                    remaining_items.append({
                        'index': i,
                        'item': item,
                        'label': display_label + content_preview
                    })

            # Застосовуємо сортування тільки до блоків, що залишилися
            if remaining_items:
                # Витягуємо тільки мітки для передачі в sort_items
                labels_only = [item_info['label'] for item_info in remaining_items]
                sorted_labels = sort_items(labels_only, direction="vertical")
            else:
                sorted_labels = []

            # 2. Визначаємо впорядкований список
            ordered_content = []
            if sorted_labels and len(sorted_labels) > 0:
                # Відновлюємо порядок елементів на основі відсортованих міток
                for label in sorted_labels:
                    # Знайдемо відповідний елемент у списку, що залишилися
                    for item_info in remaining_items:
                        if item_info['label'] == label:
                            ordered_content.append(item_info['item'])
                            break
            else:
                # Якщо сортування не застосовувалося, просто виключаємо видалені
                ordered_content = [item for i, item in enumerate(sorted_selected_content) if i not in st.session_state['deleted_blocks']]

            # 3. Редагування контенту (ВИДАЛЕНО ЗА ЗАПИТОМ)
            # st.markdown("### ✏️ Редагування вмісту")
            # ...
            pass
        else:
            ordered_content = []

        # Секція 6: Перетин кордону України
        st.markdown("---")
        # Секція 6: Додаткові дані (ДМС та Аркан)
        st.markdown("---")
        st.header("6️⃣ Документи")
        
        tab_dms, tab_arkan, tab_real_estate, tab_car = st.tabs(["🏛️ ДМС", "🚢 Аркан", "🏢 Нерухомість", "🚗 АВТО"])

        with tab_dms:
            uploaded_dms = st.file_uploader(
                "Завантажте PDF файл (ДМС)",
                type=['pdf'],
                key="dms_pdf_uploader"
            )

            if uploaded_dms:
                if st.session_state.get('last_uploaded_dms') != uploaded_dms.name:
                    with st.spinner("Обробка PDF ДМС..."):
                        dms_info, photo_bytes, error = extract_dms_data(uploaded_dms)
                        if error:
                            st.error(error)
                        else:
                            st.success(f"✅ Дані з файлу {uploaded_dms.name} успішно зчитано")
                            st.session_state['dms_data'] = {
                                'info': dms_info,
                                'photo_bytes': photo_bytes
                            }
                            st.session_state['last_uploaded_dms'] = uploaded_dms.name
                            if photo_bytes:
                                st.session_state['photo_data'] = base64.b64encode(photo_bytes).decode()

            if st.session_state.get('dms_data'):
                st.info(f"📁 Використовуються дані ДМС з: {st.session_state.get('last_uploaded_dms')}")
                if st.button("❌ Очистити дані ДМС"):
                    st.session_state['dms_data'] = None
                    st.session_state['last_uploaded_dms'] = None
                    st.rerun()

        with tab_arkan:
            uploaded_excel = st.file_uploader(
                "Завантажте Excel файл (Аркан)",
                type=['xlsx', 'xls'],
                key="arkan_excel_uploader"
            )

            if uploaded_excel:
                if st.session_state.get('last_uploaded_arkan') != uploaded_excel.name:
                    with st.spinner("Обробка Excel файлу..."):
                        border_data, error = process_excel_to_data(uploaded_excel)
                        if error:
                            st.error(error)
                        else:
                            st.success(f"✅ Дані з файлу {uploaded_excel.name} успішно зчитано")
                            st.session_state['border_crossing_data'] = border_data
                            st.session_state['last_uploaded_arkan'] = uploaded_excel.name

            if st.session_state.get('border_crossing_data'):
                st.info(f"📁 Використовуються дані Аркан з: {st.session_state.get('last_uploaded_arkan')}")
                if st.button("❌ Очистити дані Аркан"):
                    st.session_state['border_crossing_data'] = None
                    st.session_state['last_uploaded_arkan'] = None
                    st.rerun()

        with tab_real_estate:
            uploaded_real_estate = st.file_uploader(
                "Завантажте PDF файл (Нерухомість)",
                type=['pdf'],
                accept_multiple_files=True,
                key="real_estate_pdf_uploader"
            )

            if uploaded_real_estate:
                if st.session_state.get('last_uploaded_real_estate') != uploaded_real_estate[0].name:
                    with st.spinner("Обробка PDF файлів нерухомості..."):
                        all_real_estate_data = []
                        
                        for uploaded_file in uploaded_real_estate:
                            # Seek to the beginning of the file
                            uploaded_file.seek(0)
                            
                            real_estate_data, error = parse_real_estate_pdf(uploaded_file)
                            
                            if error:
                                st.error(f"Помилка обробки файлу {uploaded_file.name}: {error}")
                            else:
                                if real_estate_data:
                                    all_real_estate_data.extend(real_estate_data)
                        
                        if all_real_estate_data:
                            st.session_state['real_estate_data'] = all_real_estate_data
                            st.success(f"✅ Дані з файлів нерухомості успішно зчитано. Знайдено {len(all_real_estate_data)} записів.")
                        else:
                            st.warning("Не знайдено даних про нерухомість у завантажених файлах.")
                        
                        st.session_state['last_uploaded_real_estate'] = uploaded_real_estate[0].name

            if st.session_state.get('real_estate_data'):
                st.info(f"📁 Використовуються дані нерухомості")
                
                # Отображаем извлеченные данные для проверки
                with st.expander("🔍 Перегляд даних нерухомості", expanded=False):
                    real_estate_data = st.session_state['real_estate_data']
                    for idx, item in enumerate(real_estate_data):
                        st.write(f"**Об'єкт нерухомості #{idx + 1}:**")
                        for key, value in item.items():
                            if value:
                                st.write(f"- {key}: {value}")
                        st.write("---")  # Разделитель между объектами
                
                if st.button("❌ Очистити дані нерухомості"):
                    st.session_state['real_estate_data'] = None
                    st.session_state['last_uploaded_real_estate'] = None
                    st.rerun()

        with tab_car:
            # Ініціалізація session_state для даних про ТЗ
            if 'car_files_data' not in st.session_state:
                st.session_state['car_files_data'] = []
            if 'car_manual_entries' not in st.session_state:
                st.session_state['car_manual_entries'] = []

            st.markdown("##### **Або додати вручну:**")

            # Кнопка додавання запису
            if st.button("➕ Додати запис (ручний ввід)", key="add_manual_car"):
                st.session_state['car_manual_entries'].append({
                    'text': '',
                    'source': 'manual'
                })
                st.rerun()

            # Показуємо вручну додані записи
            if st.session_state.get('car_manual_entries'):
                st.markdown("**Ручний ввід:**")

                for idx in range(len(st.session_state['car_manual_entries'])):
                    item = st.session_state['car_manual_entries'][idx]

                    col1, col2 = st.columns([2, 1])

                    with col1:
                        # Текстове поле
                        text_key = f"manual_car_text_{idx}"
                        new_text = st.text_area(
                            f"Запис #{idx + 1}:",
                            value=item.get('text', ''),
                            key=text_key,
                            height=150
                        )
                        st.session_state['car_manual_entries'][idx]['text'] = new_text

                    with col2:
                        # Кнопка видалення
                        if st.button(f"❌ Видалити #{idx + 1}", key=f"delete_manual_car_{idx}"):
                            st.session_state['car_manual_entries'].pop(idx)
                            st.rerun()

            st.markdown("---")
            st.markdown("##### **Завантажити файли (Excel або текстові)**")
            uploaded_car_files = st.file_uploader(
                "Завантажте файли (Excel або текстові)",
                type=['xlsx', 'xls', 'txt'],
                accept_multiple_files=True,
                key="car_files_uploader"
            )

            # Обробка завантажених файлів
            if uploaded_car_files:
                st.write(f"🔍 Вибрано файлів: **{len(uploaded_car_files)}**")
                for f in uploaded_car_files:
                    st.write(f"   • `{f.name}`")

            if st.button("🔄 Обробити файли", type="primary", key="process_car_files_btn") and uploaded_car_files:
                with st.spinner("Обробка файлів..."):
                    all_car_data = []

                    for uploaded_file in uploaded_car_files:
                        try:
                            st.write(f"⏳ Обробка `{uploaded_file.name}`...")

                            # Визначаємо тип файлу
                            file_ext = os.path.splitext(uploaded_file.name)[1].lower()

                            if file_ext == '.txt':
                                # Текстовий файл - парсинг даних про ТЗ
                                content = uploaded_file.read().decode('utf-8')
                                car_data = parse_vehicle_data(content)
                                if car_data:
                                    car_data['source'] = 'file'
                                    car_data['filename'] = uploaded_file.name
                                    all_car_data.append(car_data)
                                    st.success(f"✅ `{uploaded_file.name}` - текстовий файл оброблено")

                            elif file_ext in ['.xls', '.xlsx', '.xlsm']:
                                # Excel файл
                                try:
                                    if file_ext == '.xls':
                                        df = pd.read_excel(uploaded_file, engine='xlrd')
                                    else:
                                        df = pd.read_excel(uploaded_file, engine='openpyxl')
                                    car_data = parse_excel_file(df)
                                    if car_data:
                                        car_data['source'] = 'file'
                                        car_data['filename'] = uploaded_file.name
                                        all_car_data.append(car_data)
                                        st.success(f"✅ `{uploaded_file.name}` - Excel файл оброблено")
                                except Exception as e:
                                    st.error(f"❌ Помилка читання Excel `{uploaded_file.name}`: {e}")
                                    # Пробуємо як текст
                                    try:
                                        uploaded_file.seek(0)
                                        content = uploaded_file.read().decode('utf-8', errors='ignore')
                                        car_data = parse_vehicle_data(content)
                                        if car_data:
                                            car_data['source'] = 'file'
                                            car_data['filename'] = uploaded_file.name
                                            all_car_data.append(car_data)
                                    except Exception as e2:
                                        st.error(f"❌ Помилка обробки `{uploaded_file.name}` як текст: {e2}")

                            else:
                                st.warning(f"⚠️ Невідомий формат файлу `{uploaded_file.name}`")

                        except Exception as e:
                            st.error(f"❌ Помилка обробки файлу `{uploaded_file.name}`: {e}")

                    if all_car_data:
                        st.session_state['car_files_data'].extend(all_car_data)
                        st.success(f"✅ Всього оброблено: {len(all_car_data)} записів")
                        st.rerun()
                    elif not all_car_data:
                        st.warning("⚠️ Не вдалося витягти дані з жодного файлу. Перевірте формат даних.")

            # Об'єднуємо дані з файлів та ручного вводу
            all_car_results = []

            # Додаємо дані з файлів
            for item in st.session_state.get('car_files_data', []):
                all_car_results.append(item)

            # Додаємо дані з ручного вводу
            for item in st.session_state.get('car_manual_entries', []):
                if item.get('text'):
                    parsed_data = parse_vehicle_data(item['text'])
                    if parsed_data:
                        parsed_data['source'] = 'manual'
                        all_car_results.append(parsed_data)

            if all_car_results:
                st.info(f"📊 Всього записів про ТЗ: {len(all_car_results)}")

                # Відображаємо результати
                for idx, item in enumerate(all_car_results):
                    with st.expander(f"🚗 ТЗ #{idx + 1}", expanded=False):
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.write("**Поля:**")
                            for key, value in item.items():
                                if key not in ['source', 'filename'] and value:
                                    st.write(f"• **{key}:** {value}")

                            if item.get('source') == 'file':
                                st.write(f"• **Джерело:** Файл `{item.get('filename', '')}`")
                            else:
                                st.write(f"• **Джерело:** Ручний ввід")

                        with col2:
                            # Форматований вивід
                            formatted_parts = []
                            if item.get('номерний_знак'):
                                formatted_parts.append(f"Номерний знак: {item['номерний_знак']}")
                            if item.get('марка') or item.get('модель'):
                                brand_model = f"{item.get('марка', '')} {item.get('модель', '')}".strip()
                                formatted_parts.append(f"ТЗ: {brand_model}")
                            if item.get('vin'):
                                formatted_parts.append(f"VIN: {item['vin']}")
                            if item.get('колір'):
                                formatted_parts.append(f"Колір: {item['колір']}")
                            
                            if item.get('рік_випуску'):
                                formatted_parts.append(f"Рік випуску: {item['рік_випуску']}")

                            formatted_text = ', '.join(formatted_parts) + '.' if formatted_parts else 'Немає даних'
                            st.success(formatted_text)

            # Зберігаємо об'єднані дані в session_state для експорту
            if all_car_results:
                st.session_state['combined_car_data'] = all_car_results
            else:
                st.session_state['combined_car_data'] = None

            # Кнопка очищення
            if st.button("🧹 Очистити всі дані про ТЗ", key="clear_all_car_data"):
                st.session_state['car_files_data'] = []
                st.session_state['car_manual_entries'] = []
                st.session_state['combined_car_data'] = None
                st.rerun()

        # Секція 7: Родинні зв'язки
        st.markdown("---")
        st.header("7️⃣ Родинні зв'язки")

        relatives = ["Дружина", "Чоловік", "Син", "Донька", "Мати", "Батько", "Родич"]
        family_tabs = st.tabs([f"👤 {r}" for r in relatives])

        if 'family_data' not in st.session_state:
            st.session_state['family_data'] = {}

        if 'family_manual_data' not in st.session_state:
            st.session_state['family_manual_data'] = {}

        for i, relative_type in enumerate(relatives):
            with family_tabs[i]:
                st.markdown("##### **Завантажити PDF файли (ДМС)**")
                uploaded_family_pdfs = st.file_uploader(
                    f"Завантажте PDF файли ДМС ({relative_type})",
                    type=['pdf'],
                    accept_multiple_files=True,
                    key=f"family_pdf_{relative_type}"
                )

                # Обробка завантажених файлів
                if uploaded_family_pdfs:
                    files_key = f"last_uploaded_family_{relative_type}"
                    current_files = [f.name for f in uploaded_family_pdfs]
                    last_files = st.session_state.get(files_key, [])

                    if current_files != last_files:
                        with st.spinner(f"Обробка PDF файлів {relative_type}..."):
                            if relative_type not in st.session_state['family_data']:
                                st.session_state['family_data'][relative_type] = []

                            for pdf_file in uploaded_family_pdfs:
                                dms_info, photo_bytes, error = extract_dms_data(pdf_file)
                                if error:
                                    st.error(f"Помилка у файлі {pdf_file.name}: {error}")
                                else:
                                    st.success(f"✅ Дані родича ({relative_type}) з файлу {pdf_file.name} успішно зчитано")
                                    st.session_state['family_data'][relative_type].append({
                                        'info': dms_info,
                                        'photo_bytes': photo_bytes,
                                        'source': 'pdf',
                                        'filename': pdf_file.name
                                    })

                            st.session_state[files_key] = current_files

                # Показуємо завантажені дані
                if relative_type in st.session_state['family_data'] and st.session_state['family_data'][relative_type]:
                    st.markdown("##### **Завантажені дані з PDF:**")
                    for idx, item in enumerate(st.session_state['family_data'][relative_type]):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.info(f"📁 Файл: {item.get('filename', 'Невідомо')}")
                        with col2:
                            if st.button(f"❌", key=f"delete_pdf_{relative_type}_{idx}", help="Видалити"):
                                st.session_state['family_data'][relative_type].pop(idx)
                                st.rerun()

                st.markdown("---")
                st.markdown("##### **Або додати вручну:**")

                # Кнопка додавання нового запису
                if st.button(f"➕ Додати запис ({relative_type})", key=f"add_manual_{relative_type}"):
                    if relative_type not in st.session_state['family_manual_data']:
                        st.session_state['family_manual_data'][relative_type] = []
                    st.session_state['family_manual_data'][relative_type].append({
                        'text': '',
                        'photo_bytes': None
                    })
                    st.rerun()

                # Показуємо вручну додані записи
                if relative_type in st.session_state['family_manual_data'] and st.session_state['family_manual_data'][relative_type]:
                    for idx, item in enumerate(st.session_state['family_manual_data'][relative_type]):
                        st.markdown(f"**Запис #{idx + 1}:**")
                        col1, col2 = st.columns([1, 2])

                        with col1:
                            # Завантаження фото для запису
                            uploaded_photo = st.file_uploader(
                                "Фото",
                                type=['png', 'jpg', 'jpeg'],
                                key=f"manual_photo_{relative_type}_{idx}"
                            )

                            if uploaded_photo:
                                img = Image.open(uploaded_photo)
                                buffered = BytesIO()
                                img.save(buffered, format="PNG")
                                st.session_state['family_manual_data'][relative_type][idx]['photo_bytes'] = buffered.getvalue()
                                st.image(img, width=150)
                            elif item.get('photo_bytes'):
                                st.image(Image.open(BytesIO(item['photo_bytes'])), width=150)
                            elif os.path.exists('default_avatar.png'):
                                st.image('default_avatar.png', width=150)

                        with col2:
                            # Текстове поле для введення даних
                            text_key = f"manual_text_{relative_type}_{idx}"
                            current_text = item.get('text', '')
                            new_text = st.text_area(
                                "Текст (використовуйте формат \"Ключ: значення\" для кожного поля)",
                                value=current_text,
                                key=text_key,
                                height=150
                            )
                            st.session_state['family_manual_data'][relative_type][idx]['text'] = new_text

                        # Кнопка видалення запису
                        if st.button(f"❌ Видалити запис #{idx + 1}", key=f"delete_manual_{relative_type}_{idx}"):
                            st.session_state['family_manual_data'][relative_type].pop(idx)
                            st.rerun()

                        st.markdown("---")

        # Секція експорту
        st.markdown("---")
        st.header("8️⃣ Експорт досьє")

        if not ordered_content:
            st.info("Виберіть хоча б один блок для формування досьє")
        else:
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📥 Завантажити DOCX", type="primary"):
                    with st.spinner("Генерація DOCX..."):
                        try:
                            photo_bytes = None
                            if 'photo_data' in st.session_state:
                                photo_bytes = base64.b64decode(st.session_state['photo_data'])
                            elif os.path.exists('default_avatar.png'):
                                # Завантажуємо фото за замовчуванням
                                with open('default_avatar.png', 'rb') as f:
                                    photo_bytes = f.read()

                            family_list = []
                            if 'family_data' in st.session_state:
                                for rel_type, rel_data_list in st.session_state['family_data'].items():
                                    for rel_item in rel_data_list:
                                        family_list.append({
                                            'relative_type': rel_type,
                                            'info': rel_item['info'],
                                            'photo_bytes': rel_item['photo_bytes']
                                        })
                            # Додаємо вручну введені дані
                            if 'family_manual_data' in st.session_state:
                                for rel_type, manual_list in st.session_state['family_manual_data'].items():
                                    for manual_item in manual_list:
                                        if manual_item.get('text') or manual_item.get('photo_bytes'):
                                            family_list.append({
                                                'relative_type': rel_type,
                                                'manual_text': manual_item.get('text', ''),
                                                'photo_bytes': manual_item.get('photo_bytes')
                                            })

                            docx_data = generate_docx(
                                {"Контент": ordered_content},
                                photo_bytes=photo_bytes,
                                border_crossing_data=st.session_state.get('border_crossing_data'),
                                dms_data=st.session_state.get('dms_data'),
                                family_data=family_list,
                                real_estate_data=st.session_state.get('real_estate_data'),
                                car_data=st.session_state.get('combined_car_data')
                            )

                            # Получаем имя файла из блока "Початок документа"
                            from document_generator import get_filename_from_intro
                            filename = get_filename_from_intro({"Контент": ordered_content})

                            st.download_button(
                                label="💾 Зберегти DOCX",
                                data=docx_data,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                        except Exception as e:
                            st.error(f"❌ Помилка: {e}")

            with col2:
                if st.button("📥 Завантажити PDF", type="secondary"):
                    with st.spinner("Генерація PDF..."):
                        try:
                            photo_bytes = None
                            if 'photo_data' in st.session_state:
                                photo_bytes = base64.b64decode(st.session_state['photo_data'])
                            elif os.path.exists('default_avatar.png'):
                                # Завантажуємо фото за замовчуванням
                                with open('default_avatar.png', 'rb') as f:
                                    photo_bytes = f.read()

                            family_list = []
                            if 'family_data' in st.session_state:
                                for rel_type, rel_data in st.session_state['family_data'].items():
                                    family_list.append({
                                        'relative_type': rel_type,
                                        'info': rel_data['info'],
                                        'photo_bytes': rel_data['photo_bytes']
                                    })

                            family_list = []
                            if 'family_data' in st.session_state:
                                for rel_type, rel_data_list in st.session_state['family_data'].items():
                                    for rel_item in rel_data_list:
                                        family_list.append({
                                            'relative_type': rel_type,
                                            'info': rel_item['info'],
                                            'photo_bytes': rel_item['photo_bytes']
                                        })
                            # Додаємо вручну введені дані
                            if 'family_manual_data' in st.session_state:
                                for rel_type, manual_list in st.session_state['family_manual_data'].items():
                                    for manual_item in manual_list:
                                        if manual_item.get('text') or manual_item.get('photo_bytes'):
                                            family_list.append({
                                                'relative_type': rel_type,
                                                'manual_text': manual_item.get('text', ''),
                                                'photo_bytes': manual_item.get('photo_bytes')
                                            })

                            # Пробуем создать PDF напрямую из данных
                            pdf_data = create_pdf_directly(
                                {"Контент": ordered_content},
                                photo_bytes=photo_bytes,
                                border_crossing_data=st.session_state.get('border_crossing_data'),
                                dms_data=st.session_state.get('dms_data'),
                                family_data=family_list,
                                real_estate_data=st.session_state.get('real_estate_data'),
                                car_data=st.session_state.get('combined_car_data')
                            )

                            # Отримуємо ім'я PDF-файлу
                            pdf_filename = get_pdf_filename_from_intro({"Контент": ordered_content})

                            st.download_button(
                                label="💾 Зберегти PDF(ІПНП) ",
                                data=pdf_data,
                                file_name=pdf_filename,
                                mime="application/pdf"
                            )
                        except Exception as e:
                            st.error(f"❌ Помилка при створенні PDF: {e}")
                            # Якщо пряме створення не працює, використовуємо резервний метод
                            try:
                                st.info("Спробуємо альтернативний метод конвертації...")

                                photo_bytes = None
                                if 'photo_data' in st.session_state:
                                    photo_bytes = base64.b64decode(st.session_state['photo_data'])
                                elif os.path.exists('default_avatar.png'):
                                    # Завантажуємо фото за замовчуванням
                                    with open('default_avatar.png', 'rb') as f:
                                        photo_bytes = f.read()

                                # Спочатку генеруємо DOCX
                                family_list = []
                                if 'family_data' in st.session_state:
                                    for rel_type, rel_data_list in st.session_state['family_data'].items():
                                        for rel_item in rel_data_list:
                                            family_list.append({
                                                'relative_type': rel_type,
                                                'info': rel_item['info'],
                                                'photo_bytes': rel_item['photo_bytes']
                                            })
                                # Додаємо вручну введені дані
                                if 'family_manual_data' in st.session_state:
                                    for rel_type, manual_list in st.session_state['family_manual_data'].items():
                                        for manual_item in manual_list:
                                            if manual_item.get('text') or manual_item.get('photo_bytes'):
                                                family_list.append({
                                                    'relative_type': rel_type,
                                                    'manual_text': manual_item.get('text', ''),
                                                    'photo_bytes': manual_item.get('photo_bytes')
                                                })

                                docx_data = generate_docx(
                                    {"Контент": ordered_content},
                                    photo_bytes=photo_bytes,
                                    border_crossing_data=st.session_state.get('border_crossing_data'),
                                    dms_data=st.session_state.get('dms_data'),
                                    family_data=family_list,
                                    real_estate_data=st.session_state.get('real_estate_data'),
                                    car_data=st.session_state.get('combined_car_data')
                                )

                                # Потім конвертуємо в PDF
                                pdf_data = convert_docx_to_pdf(docx_data)

                                # Отримуємо ім'я PDF-файлу из имени DOCX-файла
                                from document_generator import get_filename_from_intro
                                docx_filename = get_filename_from_intro({"Контент": ordered_content})
                                pdf_filename = get_pdf_filename_from_docx(docx_filename)

                                st.download_button(
                                    label="💾 Зберегти PDF (альтернативний метод)",
                                    data=pdf_data,
                                    file_name=pdf_filename,
                                    mime="application/pdf"
                                )
                            except Exception as backup_e:
                                st.error(f"❌ Помилка при альтернативній конвертації в PDF: {backup_e}")


            # Кнопка для повного очищення
            st.markdown("---")
            if st.button("🧹 Завершити та очистити все", help="Це видалить усі тимчасові фото та скине вибір"):
                cleanup_temp_photos() # Видаляємо ВСІ тимчасові фото
                # Очищаємо сесію (залишаємо лише службові змінні)
                keys_to_keep = ['processing_done', 'all_paragraphs']
                for key in list(st.session_state.keys()):
                    if key not in keys_to_keep:
                        del st.session_state[key]
                st.rerun()

    else:
        # Показуємо інструкцію, якщо файли ще не завантажені
        st.info("👆 Завантажте PDF файли для початку роботи")


if __name__ == "__main__":
    st.set_page_config(
        page_title="Генератор досьє з PDF",
        page_icon="📄",
        layout="wide"
    )
    # Перевіряємо наявність default_avatar.png
    if not os.path.exists('default_avatar.png'):
        st.warning("⚠️ Файл default_avatar.png не знайдено. Створіть його або завантажте власне фото.")

    main()
