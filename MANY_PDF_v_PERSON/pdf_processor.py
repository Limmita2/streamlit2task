import re
from typing import Dict, List, Any
import pdfplumber
from PIL import Image
import io



def normalize_line_breaks(text: str) -> str:
    """
    Очищає текст від небажаних підписів та нормалізує переноси рядків.
    Маркери (круглі точки, квадрати тощо) стають початком нового абзацу.
    """
    if not text:
        return ""
    
    # Видалення специфічних підписів
    unwanted = [
        "© Департамент інформаційно-аналітичної підтримки - ІПНП",
        "© Департамент інформаційно-аналітичної підтримки",
        "(cid:127)" # Часто PDF кодує буллити через cid
    ]
    for u in unwanted:
        text = text.replace(u, "")
    
    # Список маркерів видалено за запитом користувача
    
    # Замінюємо переноси рядків на пробіли, щоб отримати суцільний текст
    text = text.replace('\n', ' ')
    
    # Видаляємо подвійні пробіли
    text = re.sub(r' +', ' ', text)
    
    return text.strip()


def extract_text_from_pdf(pdf_file) -> str:
    """
    Витягує текст з PDF файлу за допомогою pdfplumber.
    
    Args:
        pdf_file: Завантажений PDF файл
        
    Returns:
        str: Витягнутий текст
    """
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Помилка при витягуванні тексту: {e}")
    
    return text




def extract_entities(text: str) -> Dict[str, Any]:
    """
    Витягує структуровані дані з тексту за допомогою регулярних виразів.
    
    Args:
        text: Текст для обробки
        
    Returns:
        Dict: Словник з витягнутими даними
    """
    entities = {
        "ПІБ": [],
        "Дата народження": [],
        "Адреси": [],
        "Телефони": [],
        "Email": [],
        "Документи": [],
        "Місця роботи": [],
        "Інша інформація": []
    }
    
    # Пошук дат народження (різні формати)
    date_patterns = [
        r'\b\d{2}\.\d{2}\.\d{4}\b',  # ДД.ММ.РРРР
        r'\b\d{2}/\d{2}/\d{4}\b',    # ДД/ММ/РРРР
        r'\b\d{2}-\d{2}-\d{4}\b',    # ДД-ММ-РРРР
    ]
    for pattern in date_patterns:
        dates = re.findall(pattern, text)
        entities["Дата народження"].extend(dates)
    
    # Пошук телефонів
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{2}[-.\s]?\d{2}\b',
    ]
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        entities["Телефони"].extend(phones)
    
    # Пошук email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    entities["Email"].extend(emails)
    
    # Пошук номерів документів (паспорт, ID)
    doc_patterns = [
        r'(?:паспорт|passport|ID|ідентифікаційний код)[\s:№#]*([A-ZА-ЯІЇЄҐ]{2}\d{6}|\d{9,10})',
        r'\b[A-ZА-ЯІЇЄҐ]{2}\s?\d{6}\b',  # Серія та номер паспорта
        r'\b\d{10}\b',  # ІПН
    ]
    for pattern in doc_patterns:
        docs = re.findall(pattern, text, re.IGNORECASE)
        if isinstance(docs[0] if docs else None, tuple):
            docs = [d[0] if isinstance(d, tuple) else d for d in docs]
        entities["Документи"].extend(docs)
    
    # Пошук ПІБ (спрощений варіант - 2-3 слова з великої літери)
    # Виключаємо слова, які часто зустрічаються в заголовках
    exclude_words = {
        'Дата', 'Народження', 'Місце', 'Роботи', 'Посада', 'Адреса', 'Проживання', 
        'Телефон', 'Мобільний', 'Домашній', 'Робочий', 'Email', 'Пошта', 
        'Паспорт', 'Серія', 'Номер', 'Виданий', 'Код', 'Ідентифікаційний',
        'Особиста', 'Картка', 'Досьє', 'Інформація', 'Про', 'Особу',
        'Відомості', 'Громадянство', 'Україна', 'Реєстрація', 'Фактична'
    }
    
    name_pattern = r'\b[А-ЯІЇЄҐA-Z][а-яіїєґa-z]+\s+[А-ЯІЇЄҐA-Z][а-яіїєґa-z]+(?:\s+[А-ЯІЇЄҐA-Z][а-яіїєґa-z]+)?\b'
    names = re.findall(name_pattern, text)
    
    filtered_names = []
    for name in names:
        # Перевірка довжини
        if not (5 < len(name) < 60):
            continue
            
        # Перевірка на входження слів з виключень
        parts = name.split()
        if any(part in exclude_words for part in parts):
            continue
            
        filtered_names.append(name)
        
    entities["ПІБ"].extend(filtered_names)
    
    # Пошук адрес (спрощений - шукаємо рядки з ключовими словами)
    address_keywords = ['вул.', 'вулися', 'проспект', 'пров.', 'провулок', 'площа', 'бульвар', 'місто', 'м.', 'с.', 'село', 'область']
    lines = text.split('\n')
    for line in lines:
        if any(keyword in line.lower() for keyword in address_keywords):
            # Очищаємо та додаємо
            clean_line = line.strip()
            # Перевіряємо щоб це не була просто назва поля
            if 10 < len(clean_line) < 200 and not clean_line.lower().endswith(':'):
                entities["Адреси"].append(clean_line)
    
    # Пошук місць роботи (рядки з ключовими словами)
    work_keywords = ['працює', 'робота', 'посада', 'організація', 'підприємство', 'компанія', 'ТОВ', 'ПП', 'ПАТ', 'директор', 'менеджер', 'керівник']
    for line in lines:
        if any(keyword in line.lower() for keyword in work_keywords):
            clean_line = line.strip()
            if 10 < len(clean_line) < 200 and not clean_line.lower().endswith(':'):
                entities["Місця роботи"].append(clean_line)
    
    return entities


def deduplicate_data(all_entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Об'єднує та видаляє дублікати з кількох наборів даних.
    
    Args:
        all_entities: Список словників з витягнутими даними
        
    Returns:
        Dict: Об'єднаний словник без дублікатів
    """
    merged = {
        "ПІБ": [],
        "Дата народження": [],
        "Адреси": [],
        "Телефони": [],
        "Email": [],
        "Документи": [],
        "Місця роботи": [],
        "Інша інформація": []
    }
    
    # Об'єднуємо всі дані
    for entities in all_entities:
        for key in merged.keys():
            if key in entities:
                merged[key].extend(entities[key])
    
    # Видаляємо дублікати, зберігаючи порядок
    for key in merged.keys():
        # Нормалізуємо (прибираємо зайві пробіли, приводимо до нижнього регістру для порівняння)
        seen = set()
        unique_items = []
        for item in merged[key]:
            # Нормалізуємо для порівняння
            normalized = ' '.join(str(item).split()).lower()
            if normalized not in seen and normalized:
                seen.add(normalized)
                unique_items.append(item)
        merged[key] = unique_items
    
    return merged


def get_pdf_paragraphs(pdf_file) -> List[Dict[str, str]]:
    """
    Витягує текст з PDF та розбиває його на блоки, базуючись на сірих полосах (rects).
    Текст без полос автоматично об'єднується з попереднім блоком.
    """
    blocks = []
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_width = float(page.width)
                header_rects = []
                for rect in page.rects:
                    w = rect['x1'] - rect['x0']
                    h = rect['y1'] - rect['y0']
                    if w > page_width * 0.4 and 8 < h < 40:
                        header_rects.append(rect)
                
                header_rects.sort(key=lambda r: r['top'])
                
                if not header_rects:
                    # Якщо смуг не знайдено, додаємо весь текст до ОСТАННЬОГО існуючого блоку
                    text = page.extract_text()
                    if text:
                        if blocks:
                            blocks[-1]["content"] += "\n" + text.strip()
                        else:
                            blocks.append({"header": "Початок документа", "content": text.strip()})
                    continue
                
                # Обробляємо текст ДО першої смуги на цій сторінці
                first_rect = header_rects[0]
                if first_rect['top'] > 20:
                    top_area = (0, 0, page_width, first_rect['top'])
                    top_text = page.within_bbox(top_area).extract_text()
                    if top_text and top_text.strip():
                        if blocks:
                            blocks[-1]["content"] += "\n" + top_text.strip()
                        else:
                            blocks.append({"header": "Початок документа", "content": top_text.strip()})

                # Обробляємо текст за смугами
                for i in range(len(header_rects)):
                    current_rect = header_rects[i]
                    next_rect = header_rects[i+1] if i + 1 < len(header_rects) else None
                    
                    header_area = (current_rect['x0']-2, current_rect['top']-2, current_rect['x1']+2, current_rect['bottom']+2)
                    header_text = page.within_bbox(header_area).extract_text() or ""
                    
                    limit_bottom = next_rect['top'] if next_rect else page.height
                    content_area = (0, current_rect['bottom'], page_width, limit_bottom)
                    content_text = page.within_bbox(content_area).extract_text() or ""
                    
                    if header_text.strip():
                        blocks.append({
                            "header": " ".join(header_text.split()),
                            "content": content_text.strip()
                        })
                    elif content_text.strip() and blocks:
                        # Якщо заголовка немає (дивно, але про всяк випадок), додаємо до попереднього
                        blocks[-1]["content"] += "\n" + content_text.strip()
                        
    except Exception as e:
        print(f"Помилка при витягуванні за смугами: {e}")
        return [{"header": "Помилка", "content": f"Не вдалося обробити: {str(e)}"}]
    
    # Фінальна чистка та нормалізація розривів
    processed_blocks = []
    for b in blocks:
        h = b["header"].strip()
        c = b["content"].strip()
        if h or c:
            clean_header = normalize_line_breaks(h)
            clean_content = normalize_line_breaks(c)
            
            
            processed_blocks.append({
                "header": clean_header,
                "content": clean_content
            })
    return processed_blocks


def process_pdfs_to_paragraphs(pdf_files) -> Dict[str, List[str]]:
    """
    Обробляє кілька PDF файлів та повертає словник {назва_файлу: [абзаци]}.
    """
    result = {}
    for pdf_file in pdf_files:
        paragraphs = get_pdf_paragraphs(pdf_file)
        result[pdf_file.name] = paragraphs
        pdf_file.seek(0)
    return result
