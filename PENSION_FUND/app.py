import re
import json
import datetime
import requests
import urllib3
import streamlit as st
from dataclasses import dataclass, asdict
from typing import Optional

urllib3.disable_warnings()

# ── Конфіг із secrets.toml ────────────────────
FINAP_URL   = st.secrets.get("FINAP_URL",     "https://finap.com.ua:9443/api")
ID_SUBJECT  = st.secrets.get("ID_SUBJECT_FM", "ERDF_api")
TOKKEN      = st.secrets.get("TOKKEN",        "")
LISTDATA    = 4_194_304  # edrfullinfo

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
    last_pos = 0
    for kw in HEADER_KEYWORDS:
        idx = text.rfind(kw)
        if idx != -1:
            end = idx + len(kw)
            if end > last_pos:
                last_pos = end
    return text[last_pos:].strip()

def parse_insurance_text(text: str) -> InsuranceRecord:
    data = strip_header(text)
    date_match = re.search(r"\b(\d{2}\.\d{2}\.\d{4})\b", data)
    date = date_match.group(1) if date_match else None
    code_match = re.search(r"\b(\d{10}|\d{8})\b", data)
    edrpou = code_match.group(1) if code_match else None
    company_name = None
    if code_match:
        raw = data[:code_match.start()].strip().strip("-–").strip()
        company_name = raw if raw else None
    return InsuranceRecord(company_name=company_name, edrpou=edrpou, last_payment_date=date)

# ══════════════════════════════════════════════
# API
# ══════════════════════════════════════════════
def query_finap(record: InsuranceRecord) -> dict:
    payload = {
        "IDinternal"  : 1,
        "DateRequest" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "IDsubjectFM" : ID_SUBJECT,
        "tokken"      : TOKKEN,
        "IDuserPC"    : 1,
        "listdata"    : LISTDATA,
    }
    if record.company_name:
        payload["name"] = record.company_name
    if record.edrpou:
        payload["ipn"] = record.edrpou

    resp = requests.post(FINAP_URL, json=payload, timeout=30, verify=False)
    resp.raise_for_status()

    parsed = resp.json()
    if isinstance(parsed, list):
        if not parsed:
            raise RuntimeError("API повернув порожній список")
        return parsed[0]
    return parsed

def parse_contacts(contacts_raw) -> dict:
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
            val   = (c.get("value") or "").strip()
            if "email" in ctype or "@" in val:
                email = val
            elif "телефон" in ctype or "phone" in ctype:
                phone = val
    return {"email": email, "phone": phone}

def extract_info(api_response: dict) -> dict:
    result  = api_response.get("result", api_response)
    if isinstance(result, str):
        raise RuntimeError(f"API повернув рядок: {result}")
    edrfull = result.get("edrfullinfo", [])
    if not edrfull:
        err = api_response.get("errormessage") or api_response.get("message", "")
        raise RuntimeError(f"Запис не знайдено в реєстрі. {err}")
    rec      = edrfull[0]
    contacts = parse_contacts(rec.get("contacts"))
    is_fop   = rec.get("type") == 0
    manager  = rec.get("manager") or (rec.get("name") if is_fop else None)
    status   = rec.get("stan") or rec.get("state") or "—"
    return {
        "name"    : rec.get("name") or rec.get("shortname") or "—",
        "address" : rec.get("address") or "—",
        "manager" : manager or "—",
        "kved"    : rec.get("kved") or "—",
        "status"  : status,
        "email"   : contacts["email"],
        "phone"   : contacts["phone"],
    }

# ══════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════
st.set_page_config(
    page_title="FinAP — Перевірка страхувальника",
    page_icon="🔍",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Unbounded:wght@400;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* Фон */
.stApp {
    background: #0D0F14;
    color: #E8EAF0;
}

/* Заголовок */
.main-title {
    font-family: 'Unbounded', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: #00E5A0;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
}
.main-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #556070;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 2rem;
}

/* Textarea */
.stTextArea textarea {
    background: #151820 !important;
    border: 1px solid #252A36 !important;
    border-radius: 8px !important;
    color: #E8EAF0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
    resize: vertical !important;
}
.stTextArea textarea:focus {
    border-color: #00E5A0 !important;
    box-shadow: 0 0 0 2px rgba(0,229,160,0.15) !important;
}

/* Кнопка */
.stButton > button {
    background: #00E5A0 !important;
    color: #0D0F14 !important;
    font-family: 'Unbounded', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.65rem 2rem !important;
    transition: opacity 0.2s !important;
    width: 100% !important;
}
.stButton > button:hover {
    opacity: 0.85 !important;
}

/* Parsed preview chips */
.chip-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin: 0.8rem 0 1.4rem;
}
.chip {
    background: #151820;
    border: 1px solid #252A36;
    border-radius: 20px;
    padding: 4px 12px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #8A94A6;
}
.chip span {
    color: #00E5A0;
    margin-left: 4px;
}

/* Картка результату */
.result-card {
    background: #151820;
    border: 1px solid #1E2430;
    border-radius: 12px;
    padding: 1.5rem 1.8rem;
    margin-top: 1rem;
}
.result-row {
    display: flex;
    align-items: flex-start;
    padding: 0.65rem 0;
    border-bottom: 1px solid #1A1F2A;
    gap: 1rem;
}
.result-row:last-child { border-bottom: none; }
.result-icon {
    font-size: 1rem;
    min-width: 24px;
    padding-top: 2px;
}
.result-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #556070;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    min-width: 130px;
}
.result-value {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.88rem;
    color: #E8EAF0;
    font-weight: 400;
    word-break: break-word;
}
.result-value.mono {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
}
.status-ok {
    display: inline-block;
    background: rgba(0,229,160,0.12);
    color: #00E5A0;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-family: 'IBM Plex Mono', monospace;
}
.status-bad {
    display: inline-block;
    background: rgba(255,80,80,0.12);
    color: #FF5050;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-family: 'IBM Plex Mono', monospace;
}

/* Hint box */
.hint-box {
    background: #0F1219;
    border-left: 3px solid #00E5A0;
    border-radius: 0 6px 6px 0;
    padding: 0.7rem 1rem;
    margin-bottom: 1rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #556070;
    line-height: 1.6;
}
.hint-box b { color: #8A94A6; }

/* Error */
.err-box {
    background: rgba(255,80,80,0.08);
    border: 1px solid rgba(255,80,80,0.25);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    color: #FF8080;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
}

/* Divider */
hr { border-color: #1E2430 !important; }

/* Hide streamlit branding */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Заголовок ─────────────────────────────────
st.markdown('<div class="main-title">🔍 FinAP Checker</div>', unsafe_allow_html=True)
st.markdown('<div class="main-sub">Перевірка страхувальника · ЄДР · CheckLists</div>', unsafe_allow_html=True)

# ── Підказка ──────────────────────────────────
st.markdown("""
<div class="hint-box">
  <b>Як використовувати:</b><br>
  Вставте рядок скопійований з реєстру <b>ІПНП (Інформаційна система "Пенсійний фонд")</b><br><br>
  Приклад повного рядка з заголовком:<br>
  <i>Назва юридичної особи... страхувальника Код ЄДРПОУ... Дата доходу <b>ФЕРМЕРСЬКЕ ГОСПОДАРСТВО "ПРОМІНЬ" 24759563 01.12.2025</b></i><br><br>
  Або скорочено (тільки дані без заголовка):<br>
  <i><b>КРЕКОТА ВІТАЛІЙ ВОЛОДИМИРОВИЧ 3433806195 01.01.2024</b></i>
</div>
""", unsafe_allow_html=True)

# ── Поле вводу ────────────────────────────────
raw_input = st.text_area(
    label="Рядок з реєстру ІПНП",
    placeholder='Вставте сюди рядок з ІПНП...\nНаприклад: ПРИВАТНЕ АКЦІОНЕРНЕ ТОВАРИСТВО "ІСРЗ" 32333962 01.08.2014',
    height=110,
    label_visibility="collapsed",
)

# ── Попередній перегляд розпарсеного ──────────
if raw_input.strip():
    rec = parse_insurance_text(raw_input.strip())
    code_label = "РНОКПП" if (rec.edrpou and len(rec.edrpou) == 10) else "ЄДРПОУ"
    chips_html = '<div class="chip-row">'
    chips_html += f'<div class="chip">🏢 Назва<span>{rec.company_name or "—"}</span></div>'
    chips_html += f'<div class="chip">🔢 {code_label}<span>{rec.edrpou or "—"}</span></div>'
    chips_html += f'<div class="chip">📅 Дата внеску<span>{rec.last_payment_date or "—"}</span></div>'
    chips_html += '</div>'
    st.markdown(chips_html, unsafe_allow_html=True)

    # ── Кнопка пошуку ─────────────────────────
    if st.button("🔎  Перевірити в FinAP"):
        if not rec.edrpou:
            st.markdown('<div class="err-box">⚠️ Не вдалося знайти ЄДРПОУ або РНОКПП у введеному тексті.</div>', unsafe_allow_html=True)
        else:
            with st.spinner("Запит до FinAP CheckLists..."):
                try:
                    api_resp = query_finap(rec)
                    info     = extract_info(api_resp)

                    # Статус badge
                    status_val = info["status"]
                    if "ЗАРЕЄСТРОВАНО" in status_val.upper() and "ПРИПИНЕНО" not in status_val.upper():
                        status_html = f'<span class="status-ok">{status_val}</span>'
                    else:
                        status_html = f'<span class="status-bad">{status_val}</span>'

                    email_val = info["email"] or "—"
                    phone_val = info["phone"] or "—"

                    card = f"""
<div class="result-card">
  <div class="result-row">
    <div class="result-icon">🏢</div>
    <div class="result-label">Назва</div>
    <div class="result-value">{info['name']}</div>
  </div>
  <div class="result-row">
    <div class="result-icon">🔢</div>
    <div class="result-label">{code_label}</div>
    <div class="result-value mono">{rec.edrpou}</div>
  </div>
  <div class="result-row">
    <div class="result-icon">📍</div>
    <div class="result-label">Адреса</div>
    <div class="result-value">{info['address']}</div>
  </div>
  <div class="result-row">
    <div class="result-icon">👤</div>
    <div class="result-label">Керівник</div>
    <div class="result-value">{info['manager']}</div>
  </div>
  <div class="result-row">
    <div class="result-icon">🏭</div>
    <div class="result-label">Вид діяльності</div>
    <div class="result-value">{info['kved']}</div>
  </div>
  <div class="result-row">
    <div class="result-icon">📊</div>
    <div class="result-label">Статус</div>
    <div class="result-value">{status_html}</div>
  </div>
  <div class="result-row">
    <div class="result-icon">📧</div>
    <div class="result-label">Email</div>
    <div class="result-value mono">{email_val}</div>
  </div>
  <div class="result-row">
    <div class="result-icon">📞</div>
    <div class="result-label">Телефон</div>
    <div class="result-value mono">{phone_val}</div>
  </div>
  <div class="result-row">
    <div class="result-icon">📅</div>
    <div class="result-label">Остання дата внеску</div>
    <div class="result-value mono">{rec.last_payment_date or '—'}</div>
  </div>
</div>
"""
                    st.markdown(card, unsafe_allow_html=True)

                    # Інформація з ПФУ в одну строку
                    pfu_line = (
                        f"Інформація з ПФУ: Останній страховий внесок був {rec.last_payment_date or '—'}. "
                        f"Оплату провів {info['name']}, РНОКПП: {rec.edrpou or '—'}, "
                        f"Адреса: {info['address']}, Керівник: {info['manager']}, "
                        f"Вид діяльності: {info['kved']}, Статус: {info['status']}, "
                        f"Email: {email_val}, Телефон: {phone_val}"
                    )
                    st.markdown(f"<div class='result-value' style='margin-top: 1rem; font-size: 0.85rem;'>{pfu_line}</div>", unsafe_allow_html=True)

                except Exception as e:
                    st.markdown(f'<div class="err-box">❌ Помилка: {e}</div>', unsafe_allow_html=True)
else:
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("🔎  Перевірити в FinAP", disabled=True)
