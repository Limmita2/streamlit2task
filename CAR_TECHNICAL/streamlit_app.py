import streamlit as st
import pandas as pd
import re
import os

st.set_page_config(page_title="Парсер реєстрації ТЗ", page_icon="🚗")

st.title("🚗 Парсер даних реєстрації транспортного засобу")

st.markdown("""
Цей додаток витягує інформацію про транспортний засіб з файлу або тексту.
""")

def parse_vehicle_data(text):
    """Парсить текст та витягує дані про ТЗ"""
    result = {}
    
    # Шаблони для пошуку
    patterns = {
        'номерний_знак': [
            r'Державний номер[:\s]*([A-ZА-ЯІЇЄ0-9]+)',
            r'Номерний знак[:\s]*([A-ZА-ЯІЇЄ0-9]+)',
            r'НОМЕРНИЙ ЗНАК[:\s]*([A-ZА-ЯІЇЄ0-9]+)',
        ],
        'власник': [
            r'Власник[:\s]*([A-ZА-ЯІЇЄ\s]+?)(?=\s*\d{2}\.\d{2}\.\d{4}|\s*$)',
        ],
        'дата_народження': [
            r'Дата народження[:\s]*(\d{2}\.\d{2}\.\d{4})',
            r'Власник[:\s]*[A-ZА-ЯІЇЄ\s]+(\d{2}\.\d{2}\.\d{4})',
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
            r'Колір ТЗ[:\s]*([A-ZА-ЯІЇЄ]+)',
            r'Колір[:\s]*([A-ZА-ЯІЇЄ]+)',
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
                    match = re.search(r'Власник[:\s]*([A-ZА-ЯІЇЄ\s]+)', cell_str)
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
                
                # Місце реєстрації (для файлу)
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
    
    # Якщо не знайшли через структуру, шукаємо через текст
    if not result:
        result = parse_vehicle_data(text)
    
    # Дозаповнюємо пропущені поля з тексту (КРІМ місця реєстрації для файлу)
    text_result = parse_vehicle_data(text)
    for key, value in text_result.items():
        if key not in result or not result[key]:
            result[key] = value
    
    return result

def format_output(data):
    """Форматує дані в одне речення"""
    parts = []
    
    if data.get('номерний_знак'):
        parts.append(f"Номерний знак: {data['номерний_знак']}")
    
    if data.get('власник'):
        owner = data['власник']
        if data.get('дата_народження'):
            owner += f" ({data['дата_народження']})"
        parts.append(f"власник: {owner}")
    
    if data.get('іпн'):
        parts.append(f"ІПН: {data['іпн']}")
    
    if data.get('місце_реєстрації'):
        parts.append(f"місце реєстрації: {data['місце_реєстрації']}")
    
    vehicle_parts = []
    if data.get('марка'):
        vehicle_parts.append(data['марка'])
    if data.get('модель'):
        vehicle_parts.append(data['модель'])
    if vehicle_parts:
        parts.append(f"марка/модель: {' '.join(vehicle_parts)}")
    
    if data.get('vin'):
        parts.append(f"VIN: {data['vin']}")
    
    if data.get('колір'):
        parts.append(f"колір: {data['колір']}")
    
    return ', '.join(parts) + '.'

# Вибір режиму вводу
input_method = st.radio("Оберіть спосіб вводу даних:", 
                        ["Текст", "Файл (Excel/XLS/XLSX)"])

extracted_data = None

if input_method == "Текст":
    raw_text = st.text_area("Вставте текст з даними про ТЗ:", height=300)
    
    if st.button("Обробити текст") and raw_text:
        extracted_data = parse_vehicle_data(raw_text)

else:  # Файл
    uploaded_file = st.file_uploader("Завантажте файл Excel", 
                                      type=['xls', 'xlsx', 'csv'])
    
    if uploaded_file is not None:
        try:
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_extension == '.csv':
                df = pd.read_csv(uploaded_file, encoding='utf-8', sep=None, engine='python')
            else:
                try:
                    df = pd.read_excel(uploaded_file, engine='openpyxl')
                except:
                    df = pd.read_excel(uploaded_file, engine='xlrd')
            
            st.subheader("📋 Попередній перегляд файлу:")
            st.dataframe(df.head(25))
            
            if st.button("Обробити файл"):
                extracted_data = parse_excel_file(df)
                
        except Exception as e:
            st.error(f"Помилка при читанні файлу: {str(e)}")

# Виведення результату
if extracted_data:
    st.subheader("📌 Витягнуті дані:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Поля:**")
        for key, value in extracted_data.items():
            st.write(f"• **{key}:** {value}")
    
    with col2:
        st.markdown("**Одне речення:**")
        formatted = format_output(extracted_data)
        st.success(formatted)
        
        st.code(formatted, language='text')

# Демо з прикладом
with st.expander("📋 Показати приклад вхідних даних"):
    example_text = """Державний номер: ВН8197ЕМ 
Свідоцтво про реєстрацію ТЗ: САТ104177 від 28.08.2013 
Попередній держ.номер: Т4ВС5586 
Марка/модель ТЗ: RENAULT MEGANE 1.4 
Категорія ТЗ: B 
Тип ТЗ: ЛЕГКОВИЙ 
Рік випуску ТЗ: 2013 
Колір ТЗ: БІЛИЙ 
vin ТЗ: VF1BZAB0649345415 
Номер кузова ТЗ: VF1BZAB0649345415 
Номер шасі ТЗ:  
Номер двигуна ТЗ: D257428 
Тип кузова ТЗ: ХЕТЧБЕК 
Класифікація ТЗ: ЗАГАЛЬНИЙ 
Об'єм двигуна: 1461 
Паливо: ДИЗЕЛЬНЕ ПАЛИВО 
Повна маса: 1780 
Власна маса: 1280 
Кількість циліндрів: 4 
Реєстраційна операція: ВТОРИННА РЕЄСТРАЦІЯ ТЗ, ПРИДБАНОГО В ТОРГОВЕЛЬНІЙ ОРГАНІЗАЦІЇ 
Адреса реєстрації ТЗ: (5104) ВРЕР №4 М. Б. ДНІСТРОВСЬК ОДЕСЬКА ОБЛ.,УКРАЇНА 
Власник: КЛИМЕНКО ВАЛЕНТИНА МИКОЛАЇВНА 01.07.1956 
ІПН/ЄДРПОУ: 2063602024 
Адреса власника: ОДЕСЬКА ОБЛ., М. БІЛГОРОД-ДНІСТРОВСЬКИЙ, СМТ ЗАТОКА, ВУЛ. ПРИМОРСЬКА, 72 
Дата першої реєстрації ТЗ: 28.08.2013"""
    
    st.code(example_text, language='text')