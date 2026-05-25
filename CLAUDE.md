# Antigravity Streamlit - Корпоративний Портал Додатків

## Огляд проекту

Це Streamlit портал для корпоративних додатків, що автоматизують обробку та аналіз даних в українському контексті. Портал об'єднує кілька інструментів для роботи з PDF, DOCX файлами, даними про нерухомість, транспорт, ДМС, Аркан та Пенсійний фонд.

**Основна мета:** Централізована платформа для створення аналітичних досьє з різних джерел даних.

## Запуск додатку

```bash
streamlit run Home.py
```

## Архітектура

### Основні компоненти

```
Antigravity_streamlit/
├── Home.py                      # Головна сторінка порталу
├── apps_config.json             # Конфігурація додатків
├── utils.py                     # Спільні утиліти
├── requirements.txt             # Python залежності
├── packages.txt                 # Системні пакети (для OCR)
├── pages/                       # Сторінки Streamlit додатків
│   ├── 1_IPNP_Application.py
│   ├── 2_BM_DOCX_Viewer.py
│   ├── 3_Person_PDF_Matcher.py
│   ├── 4_DMS_WORD_Application.py
│   ├── ARKAN_v_DOCX.py
│   ├── 5_CAR_TECHNICAL.py
│   ├── 6_REAL_ESTATE.py
│   └── 7_PENSION_FUND.py
└── MANY_PDF_v_PERSON/           # Ядро обробки документів
    ├── app.py                   # Головний додаток matcher
    ├── document_generator.py    # Генерація DOCX звітів
    ├── pdf_processor.py         # Обробка PDF
    ├── arkan_processor.py       # Обробка Аркан
    ├── dms_processor.py         # Обробка ДМС
    ├── car_processor.py         # Обробка авто
    ├── real_estate_processor.py # Обробка нерухомості
    ├── pension_processor.py     # Обробка ПФУ
    └── image_search.py          # Пошук зображень авто
```

### Додатки порталу

| Додаток | Опис | Файл |
|---------|------|------|
| IPNP Application | Обробка маршрутів з ІПНП та HTML генерацією | [IPNP_v_HTML/app.py](IPNP_v_HTML/app.py) |
| BM DOCX Viewer | Обробка архівів з БМ у форматі DOCX | [BM_v_DOCX/](BM_v_DOCX/) |
| Person PDF Matcher | Створення профілю особи з ІПНП | [MANY_PDF_v_PERSON/app.py](MANY_PDF_v_PERSON/app.py) |
| DMS v WORD | Обробка ДМС та PDF файлів у WORD | [DMS_v_WORD/](DMS_v_WORD/) |
| ARKAN v DOCX | Обробка Аркан у форматі WORD | [ARKAN_v_DOCX/](ARKAN_v_DOCX/) |
| CAR Technical | Обробка даних про транспортні засоби | [CAR_TECHNICAL/](CAR_TECHNICAL/) |
| Нерухомість | Обробка файлів нерухомості у DOCX | [Real_estate/](Real_estate/) |
| Pension Fund | Перевірка страхувальника через FinAP | [PENSION_FUND/app.py](PENSION_FUND/app.py) |

## Додавання нового додатку

1. Створіть Python файл в `pages/` або окрему папку
2. Додайте запис в `apps_config.json`:

```json
{
    "name": "Назва додатку",
    "description": "Опис функціональності",
    "page_file": "pages/ім'я_файлу.py",
    "icon": "🎯"
}
```

3. Слідкуйте за неймінгом файлів: `N_Назва.py` де N - порядковий номер

## Залежності

### Основні
- `streamlit` - Фреймворк для веб-додатків
- `pandas` - Обробка даних
- `pdfplumber` - Парсинг PDF
- `python-docx` - Створення DOCX
- `reportlab` - Генерація PDF
- `pytesseract` - OCR
- `Pillow` - Робота з зображеннями
- `openpyxl` / `xlrd` - Робота з Excel
- `beautifulsoup4` / `lxml` - Парсинг HTML
- `ddgs` / `duckduckgo-search` - Пошук зображень

### Системні пакети (packages.txt)
- `tesseract-ocr` - OCR движок
- `tesseract-ocr-ukr` - Українська мова для OCR
- `poppler-utils` - Робота з PDF
- `fonts-liberation` - Шрифти

## Стиль коду

- Використовуйте українську мову для UI елементів та коментарів
- Англійська для назв змінних, функцій та технічних термінів
- UTF-8 кодування для всіх файлів
- Форматуйте код згідно PEP 8

## Важливі патерни

### Робота з шляхами
Завжди використовуйте `os.path` для кросплатформної сумісності:

```python
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "filename.pdf")
```

### Обробка PDF
Використовуйте `pdfplumber` для тексту та `pymupdf` для швидкого перегляду.

### Генерація документів
`document_generator.py` містить функції для створення DOCX звітів - використовуйте їх як базу.

## Конфігурація

### `.streamlit/config.toml`
Налаштування теми та поведінки Streamlit.

### `apps_config.json`
Динамічна конфігурація доступних додатків на головній сторінці.

## Розгортання

### Локально
```bash
pip install -r requirements.txt
streamlit run Home.py
```

### Streamlit Cloud
1. Push to GitHub
2. Підключити репозиторій на [share.streamlit.io](https://share.streamlit.io)
3. Вказати головний файл: `Home.py`

## Примітки

- Проект використовує темну тему GitHub Dimmed
- Всі сторінки використовують `wide` layout
- Приховані меню та footer для чистого UI
- OCR функціональність вимагає встановлених системних пакетів
