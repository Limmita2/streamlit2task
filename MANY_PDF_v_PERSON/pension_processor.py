"""
Модуль обробки даних з Пенсійного фонду (ІПНП) та інтеграції з FinAP API.
"""
import re
import json
import datetime
import requests
import urllib3
from dataclasses import dataclass
from typing import Optional

urllib3.disable_warnings()


# ── Конфіг із secrets.toml ────────────────────
def get_finap_config():
    """Отримує конфігурацію FinAP з session_state або повертає значення за замовчуванням."""
    import streamlit as st
    return {
        "FINAP_URL": st.secrets.get("FINAP_URL", "https://finap.com.ua:9443/api"),
        "ID_SUBJECT": st.secrets.get("ID_SUBJECT_FM", "ERDF_api"),
        "TOKKEN": st.secrets.get("TOKKEN", ""),
        "LISTDATA": 4_194_304,
    }


# ══════════════════════════════════════════════
# ПАРСЕР
# ══════════════════════════════════════════════
HEADER_KEYWORDS = [
    "Назва юридичної особи", "страхувальника",
    "Код ЄДРПОУ", "РНОКПП", "Дата доходу",
]


@dataclass
class InsuranceRecord:
    company_name: Optional[str]
    edrpou: Optional[str]
    last_payment_date: Optional[str]


def strip_header(text: str) -> str:
    """Видаляє заголовок з тексту, залишаючи тільки дані."""
    last_pos = 0
    for kw in HEADER_KEYWORDS:
        idx = text.rfind(kw)
        if idx != -1:
            end = idx + len(kw)
            if end > last_pos:
                last_pos = end
    return text[last_pos:].strip()


def parse_insurance_text(text: str) -> InsuranceRecord:
    """Парсить текст з реєстру ІПНП та витягує дані про страхувальника."""
    data = strip_header(text)
    
    # Витягуємо дату
    date_match = re.search(r"\b(\d{2}\.\d{2}\.\d{4})\b", data)
    date = date_match.group(1) if date_match else None
    
    # Витягуємо код (ЄДРПОУ або РНОКПП)
    code_match = re.search(r"\b(\d{10}|\d{8})\b", data)
    edrpou = code_match.group(1) if code_match else None
    
    # Витягуємо назву компанії
    company_name = None
    if code_match:
        raw = data[:code_match.start()].strip().strip("-–").strip()
        company_name = raw if raw else None
    
    return InsuranceRecord(company_name=company_name, edrpou=edrpou, last_payment_date=date)


# ══════════════════════════════════════════════
# API
# ══════════════════════════════════════════════
def query_finap(record: InsuranceRecord) -> dict:
    """Відправляє запит до FinAP API для перевірки страхувальника."""
    import streamlit as st
    config = get_finap_config()
    
    payload = {
        "IDinternal": 1,
        "DateRequest": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "IDsubjectFM": config["ID_SUBJECT"],
        "tokken": config["TOKKEN"],
        "IDuserPC": 1,
        "listdata": config["LISTDATA"],
    }
    
    if record.company_name:
        payload["name"] = record.company_name
    if record.edrpou:
        payload["ipn"] = record.edrpou

    resp = requests.post(
        config["FINAP_URL"],
        json=payload,
        timeout=30,
        verify=False
    )
    resp.raise_for_status()

    parsed = resp.json()
    if isinstance(parsed, list):
        if not parsed:
            raise RuntimeError("API повернув порожній список")
        return parsed[0]
    return parsed


def parse_contacts(contacts_raw) -> dict:
    """Парсить контакти з відповіді API."""
    email, phone = None, None
    
    if not contacts_raw:
        return {"email": email, "phone": phone}
    
    if isinstance(contacts_raw, str):
        for part in [p.strip() for p in contacts_raw.split(";") if p.strip()]:
            if "@" in part:
                email = part
            elif re.search(r"[\d\-\(\)\+]", part):
                phone = part
    elif isinstance(contacts_raw, list):
        for c in contacts_raw:
            ctype = (c.get("type") or "").lower()
            val = (c.get("value") or "").strip()
            if "email" in ctype or "@" in val:
                email = val
            elif "телефон" in ctype or "phone" in ctype:
                phone = val
    
    return {"email": email, "phone": phone}


def extract_info(api_response: dict) -> dict:
    """Витягує інформацію з відповіді FinAP API."""
    result = api_response.get("result", api_response)
    
    if isinstance(result, str):
        raise RuntimeError(f"API повернув рядок: {result}")
    
    edrfull = result.get("edrfullinfo", [])
    if not edrfull:
        err = api_response.get("errormessage") or api_response.get("message", "")
        raise RuntimeError(f"Запис не знайдено в реєстрі. {err}")
    
    rec = edrfull[0]
    contacts = parse_contacts(rec.get("contacts"))
    is_fop = rec.get("type") == 0
    manager = rec.get("manager") or (rec.get("name") if is_fop else None)
    status = rec.get("stan") or rec.get("state") or "—"
    
    return {
        "name": rec.get("name") or rec.get("shortname") or "—",
        "address": rec.get("address") or "—",
        "manager": manager or "—",
        "kved": rec.get("kved") or "—",
        "status": status,
        "email": contacts["email"],
        "phone": contacts["phone"],
    }


# ══════════════════════════════════════════════
# ОСНОВНА ФУНКЦІЯ ОБРОБКИ
# ══════════════════════════════════════════════
def process_pension_data(raw_text: str) -> dict:
    """
    Обробляє текст з реєстру ІПНП та повертає дані для збереження в session_state.
    
    Returns:
        dict: {
            'raw_text': str,  # Вихідний текст
            'parsed': InsuranceRecord,  # Розпарсені дані
            'finap_info': dict,  # Дані з FinAP API
            'formatted_line': str,  # Відформатований рядок для виводу в Word
            'error': str or None  # Помилка, якщо сталася
        }
    """
    result = {
        'raw_text': raw_text,
        'parsed': None,
        'finap_info': None,
        'formatted_line': None,
        'error': None,
    }
    
    try:
        # Парсинг тексту
        parsed = parse_insurance_text(raw_text.strip())
        result['parsed'] = parsed
        
        if not parsed.edrpou:
            result['error'] = "Не вдалося знайти ЄДРПОУ або РНОКПП у введеному тексті"
            return result
        
        # Запит до FinAP API
        api_resp = query_finap(parsed)
        info = extract_info(api_resp)
        result['finap_info'] = info
        
        # Форматування рядка для виводу в Word
        code_label = "РНОКПП" if len(parsed.edrpou) == 10 else "ЄДРПОУ"
        
        formatted_line = (
            f"Інформація з ПФУ: Останній страховий внесок був {parsed.last_payment_date or '—'}. "
            f"Оплату провів {info['name']}, {code_label}: {parsed.edrpou or '—'}, "
            f"Адреса: {info['address']}, Керівник: {info['manager']}, "
            f"Вид діяльності: {info['kved']}, Статус: {info['status']}, "
            f"Email: {info['email'] or '—'}, Телефон: {info['phone'] or '—'}"
        )
        result['formatted_line'] = formatted_line
        
    except Exception as e:
        result['error'] = str(e)
    
    return result
