import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from io import BytesIO
import re


def format_text_with_styles(text, default_font, bold_font, italic_font, bold_italic_font):
    """
    Форматує текст з підтримкою різних стилів (жирний, курсив).
    """
    # Для спрощення, повертаємо текст як є
    # В реальній реалізації можна додати підтримку тегів типу <b>, <i>
    return text


def create_pdf_directly(data: dict, photo_bytes: bytes = None, border_crossing_data: list = None, dms_data: dict = None, family_data: list = None, real_estate_data: list = None, car_data: list = None) -> bytes:
    """
    Створює PDF напряму з даних, оминаючи DOCX.

    Args:
        data: Дані для генерації документа
        photo_bytes: Байти фото для вставки (опціонально)

    Returns:
        bytes: Байти PDF-документа
    """
    # Регистрируем шрифты, поддерживающие кириллицу
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    from reportlab.pdfbase.ttfonts import TTFont
    import os

    # Пути к системным шрифтам в Linux (устанавливаются через packages.txt)
    font_paths = [
        # Liberation шрифты (аналог Times New Roman)
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf',
        # DejaVu шрифты
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf',
    ]

    try:
        # Пробуем Liberation Sans
        if os.path.exists('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'):
            pdfmetrics.registerFont(TTFont('LiberationSans', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'))
            pdfmetrics.registerFont(TTFont('LiberationSans-Bold', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'))
            pdfmetrics.registerFont(TTFont('LiberationSans-Italic', '/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf'))
            pdfmetrics.registerFont(TTFont('LiberationSans-BoldItalic', '/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf'))

            default_font = 'LiberationSans'
            bold_font = 'LiberationSans-Bold'
            italic_font = 'LiberationSans-Italic'
            bold_italic_font = 'LiberationSans-BoldItalic'
        # Пробуем DejaVu Sans
        elif os.path.exists('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
            pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Oblique', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSans-BoldOblique', '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf'))

            default_font = 'DejaVuSans'
            bold_font = 'DejaVuSans-Bold'
            italic_font = 'DejaVuSans-Oblique'
            bold_italic_font = 'DejaVuSans-BoldOblique'
        else:
            raise Exception("Системные шрифты не найдены")
    except Exception as e:
        # Якщо системні шрифти недоступні, використовуємо стандартний шрифт
        print(f"Помилка завантаження шрифту: {e}")
        default_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'
        italic_font = 'Helvetica-Oblique'
        bold_italic_font = 'Helvetica-BoldOblique'

    # Створюємо PDF документ в пам'яті
    pdf_buffer = BytesIO()
    doc_template = SimpleDocTemplate(pdf_buffer, pagesize=A4, topMargin=56, bottomMargin=56,
                                     leftMargin=85, rightMargin=42)  # Конвертация из см в pt (1 см = 28.3 pt)

    # Розраховуємо ширину для таблиц на всю ширину сторінки
    page_width = 595  # Ширина A4 в пунктах (8.27 дюймів * 72 pt/inch)
    left_margin = 85  # Лівий відступ у пунктах
    right_margin = 42  # Правий відступ у пунктах
    full_width = page_width - left_margin - right_margin  # Ширина доступного простору

    # Встановлюємо стилі
    styles = getSampleStyleSheet()

    # Створюємо кастомні стилі
    title_center_style = ParagraphStyle(
        'TitleCenter',
        parent=styles['Normal'],
        fontName=default_font,
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=0,
        spaceBefore=0,
        leading=16.1  # 1,15 інтервал
    )

    title_italic_style = ParagraphStyle(
        'TitleItalic',
        parent=styles['Normal'],
        fontName=italic_font,
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=0,
        spaceBefore=0,
        leading=16.1  # 1,15 інтервал
    )

    blue_header_style = ParagraphStyle(
        'BlueHeader',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=14,
        alignment=TA_LEFT,
        textColor=colors.black,  # Змінюємо колір тексту на чорний
        backColor=colors.HexColor('#9BC2E6'),
        leftIndent=28,  # 7 пробілів (~7*4pt)
        spaceAfter=0,
        spaceBefore=0,
        leading=16.1  # 1,15 інтервал
    )

    blue_header_italic_style = ParagraphStyle(
        'BlueHeaderItalic',
        parent=styles['Normal'],
        fontName=bold_italic_font,
        fontSize=14,
        alignment=TA_LEFT,
        textColor=colors.black,  # Змінюємо колір тексту на чорний
        backColor=colors.HexColor('#9BC2E6'),
        leftIndent=28,  # 7 пробілів (~7*4pt)
        spaceAfter=0,
        spaceBefore=0,
        leading=16.1  # 1,15 інтервал
    )

    normal_justified_style = ParagraphStyle(
        'NormalJustified',
        parent=styles['Normal'],
        fontName=default_font,
        fontSize=14,
        alignment=TA_JUSTIFY,
        leftIndent=0,
        rightIndent=0,
        spaceAfter=2,
        spaceBefore=0,
        leading=16.1  # 1,15 інтервал
    )
    
    # Список елементів для побудови PDF
    elements = []
    
    # Додаємо заголовки
    elements.append(Paragraph("АНАЛІТИЧНИЙ ПРОФІЛЬ", title_center_style))
    elements.append(Paragraph("на фізичну особу", title_center_style))
    elements.append(Spacer(1, 0))  # Порожній рядок з висотою 8pt

    # 1. ЗАГАЛЬНИЙ ЗАГОЛОВОК ДОКУМЕНТА (Блакитна полоса)
    # Створюємо таблицю для заголовка з блакитним фоном
    # Використовуємо ширину всієї сторінки з урахуванням відступів
    full_width = 515  # Приблизна ширина сторінки A4 з відступами (595 - 2*40)
    header_table_data = [["       " + "АНКЕТНІ ДАНІ:"]]  # 7 пробілів перед заголовком

    header_table = Table(header_table_data, colWidths=[full_width])

    # Стиль таблиці з блакитним фоном
    header_table_style = TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), bold_italic_font),  # Жирний курсив
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGNMENT', (0, 0), (-1, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#9BC2E6')),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Прибираємо внутрішні відступи, щоб фон був під пробілами
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),  # Зменшуємо відступ згори (приблизно 1 мм)
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Збільшуємо відступ знизу (приблизно 5 мм)
        # Повністю прибираємо межі
        ('LINEBELOW', (0, 0), (-1, -1), 0, colors.white),  # Прозора межа
        ('LINEABOVE', (0, 0), (-1, -1), 0, colors.white),
        ('LINEBEFORE', (0, 0), (-1, -1), 0, colors.white),
        ('LINEAFTER', (0, 0), (-1, -1), 0, colors.white),
    ])

    header_table.setStyle(header_table_style)
    elements.append(header_table)
    elements.append(Spacer(1, 8))  # Порожній рядок висотою 8pt
    
    # Створюємо таблицю для фото та вступного тексту
    content_list = data.get("Контент", [])
    intro_text = ""
    filtered_content = []
    
    for item in content_list:
        if item.get("header") == "Початок документа" and not intro_text:
            intro_text = item.get("content", "")
        else:
            filtered_content.append(item)
    
    # Створюємо таблицю для фото та вступного тексту
    if photo_bytes or intro_text:
        # Підготуємо елементи для таблиці
        photo_cell = []
        text_cell = []

        # Додаємо фото в ліву комірку
        if photo_bytes:
            try:
                # Створюємо зображення з байтів
                img_buffer = BytesIO(photo_bytes)
                # Спробуємо створити зображення зі збереженням пропорцій
                img = Image(img_buffer, width=142, height=142)  # 1.8 дюйма * 72 pt/inch
                img.hAlign = 'LEFT'  # Вирівнювання зображення по лівому краю
                photo_cell.append(img)
            except Exception as e:
                # Якщо не вдалося додати фото, виводимо повідомлення про помилку в лог
                print(f"Ошибка при добавлении фото: {e}")
                # Замість порожньої комірки додамо текстове сповіщення
                style = ParagraphStyle(
                    'PhotoPlaceholderStyle',
                    parent=styles['Normal'],
                    fontName=default_font,
                    fontSize=10,
                    alignment=TA_LEFT,
                    leftIndent=0,
                    spaceAfter=2,
                    spaceBefore=0,
                    leading=12
                )
                photo_cell.append(Paragraph("Фото відсутнє", style))

        # Додаємо текст в праву комірку
        if intro_text:
            # Очищаємо текст від "д.н."
            intro_text = intro_text.replace("д.н.", "").replace("  ", " ")

            # Визначаємо спеціальні паттерни для "Місце народження" і "Громадянство"
            SPECIAL_PATTERN = r'([МM][іi][сc]ц[еe]\s*[нN][аa][рR][оO][дD][жJ][еЕ][нN]{2}[яY]\s*:|Громадянство\s*:)'

            # Розбиваємо текст за ключовими словами і робимо їх жирними
            BOLD_PATTERN = r'(Mарка\s*:|заявник\s*:|Марка\s*:|свідок\s*\(учасник\)\s*:|ухилянт\s*:|Вид\s*:|правопорушник\s*:|Номер\s*дозволу\s*:|телефони\s*:|[МM][іi][сc]ц[еe]\s*[нH][аa][рp][оo]др[еe][нH]{2}я\s*:|Громадянство\s*:|постраждалий\s*\(потерпілий\)\s*:|категорія\s*:|№\s+[А-ЯІЇ]{2,4}\s+\d+(?:\s+[А-ЯІЇ]{2}\s+\d+)?\s+від\s+\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}\s*,\s*орган:)'

            # Спочатку розбиваємо за спеціальними паттернами (Місце народження і Громадянство)
            special_parts = re.split(SPECIAL_PATTERN, intro_text)

            for special_part in special_parts:
                if not special_part:
                    continue

                # Перевіряємо, чи є частина спеціальним ключовим словом
                if re.fullmatch(SPECIAL_PATTERN, special_part):
                    # Жирний стиль для спеціальних ключових слів
                    style = ParagraphStyle(
                        'IntroSpecialBoldStyle',
                        parent=styles['Normal'],
                        fontName=bold_font,
                        fontSize=14,
                        alignment=TA_LEFT,  # Для вступного тексту використовуємо ліве вирівнювання
                        leftIndent=0,
                        spaceAfter=2,
                        spaceBefore=6,  # Додаємо відступ згори для нового рядка
                        leading=16.1
                    )
                    text_cell.append(Paragraph(special_part, style))
                else:
                    # Розбиваємо решту тексту за звичайними ключовими словами
                    parts = re.split(BOLD_PATTERN, special_part)

                    for part in parts:
                        if not part:
                            continue

                        # Перевіряємо, чи є частина ключовим словом
                        if re.fullmatch(BOLD_PATTERN, part):
                            # Жирний стиль для ключових слів
                            style = ParagraphStyle(
                                'IntroBoldStyle',
                                parent=styles['Normal'],
                                fontName=bold_font,
                                fontSize=14,
                                alignment=TA_LEFT,  # Для вступного тексту використовуємо ліве вирівнювання
                                leftIndent=0,
                                spaceAfter=2,
                                spaceBefore=0,
                                leading=16.1
                            )
                            text_cell.append(Paragraph(part, style))
                        else:
                            # Звичайний стиль для решти тексту
                            style = ParagraphStyle(
                                'IntroNormalStyle',
                                parent=styles['Normal'],
                                fontName=default_font,
                                fontSize=14,
                                alignment=TA_LEFT,  # Для вступного тексту використовуємо ліве вирівнювання
                                leftIndent=0,
                                spaceAfter=2,
                                spaceBefore=0,
                                leading=16.1
                            )
                            text_cell.append(Paragraph(part, style))
        else:
            style = ParagraphStyle(
                'IntroDefaultStyle',
                parent=styles['Normal'],
                fontName=default_font,
                fontSize=14,
                alignment=TA_LEFT,
                leftIndent=0,
                spaceAfter=2,
                spaceBefore=0,
                leading=16.1
            )
            text_cell.append(Paragraph("Особисте досьє", style))

        # Створюємо таблицю з двома колонками
        # 142 pt - ширина фото (1.8 дюйма), 28 pt - відступ 5 мм (5/25.4*72), 318-28=290 pt - ширина тексту
        table_data = [[photo_cell, text_cell]]
        table = Table(table_data, colWidths=[142, 290])  # 1.8 дюйма * 72 = 142 pt, залишок з урахуванням відступу

        # Стиль таблиці
        table_style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (0, -1), 4),      # Лівий відступ для фото
            ('RIGHTPADDING', (0, 0), (0, -1), 14),    # Правий відступ для фото (приблизно 5 мм)
            ('LEFTPADDING', (1, 0), (1, -1), 14),     # Лівий відступ для тексту (приблизно 5 мм)
            ('RIGHTPADDING', (1, 0), (1, -1), 4),     # Правий відступ для тексту
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ])

        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 6))  # Відступ після таблиці

    # Обробляємо інші блоки
    for item in filtered_content:
        header = item.get("header", "").strip()
        content = item.get("content", "").strip()

        if header:
            # Створюємо таблицю для заголовка з блакитним фоном на всю ширину
            header_table_data = [["       " + header.upper()]]  # 7 пробелов перед заголовком
            header_table = Table(header_table_data, colWidths=[full_width])  # Используем ту же ширину

            # Стиль таблиці з блакитним фоном
            header_table_style = TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), bold_italic_font),  # Жирний курсив
                ('FONTSIZE', (0, 0), (-1, -1), 14),
                ('ALIGNMENT', (0, 0), (-1, -1), 'LEFT'),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#9BC2E6')),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Прибираємо внутрішні відступи
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 2),  # Зменшуємо відступ згори (приблизно 1 мм)
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Збільшуємо відступ знизу (приблизно 5 мм)
                # Повністю прибираємо межі
                ('LINEBELOW', (0, 0), (-1, -1), 0, colors.white),  # Прозора межа
                ('LINEABOVE', (0, 0), (-1, -1), 0, colors.white),
                ('LINEBEFORE', (0, 0), (-1, -1), 0, colors.white),
                ('LINEAFTER', (0, 0), (-1, -1), 0, colors.white),
            ])

            header_table.setStyle(header_table_style)
            elements.append(header_table)

            if content:
                # Розбиваємо контент за абзацами
                paragraphs_list = content.split('\n')

                # Определяем паттерн для конкретного заголовка
                if header == "ЄРДР":
                    pat = r'(№\s+\d{24}\s+від\s+\d{2}\.\d{2}\.\d{4}\s*,\s*за\s*СТ\.|' + BOLD_PATTERN[1:]  # Прибираємо першу дужку
                elif header == "Адреса":
                    pat = r'(місце\s*проживання\s*:|' + BOLD_PATTERN[1:]  # Прибираємо першу дужку
                else:
                    pat = BOLD_PATTERN

                for p_text in paragraphs_list:
                    if p_text.strip():
                        # Применяем стиль с выравниванием по ширине
                        # Розбиваємо текст за ключовими словами
                        sub_parts = re.split(pat, p_text)
                        for sub_part in sub_parts:
                            if not sub_part:
                                continue

                            # Перевіряємо, чи є частина ключовим словом
                            if re.fullmatch(pat, sub_part):
                                # Жирний стиль для ключових слів
                                style = ParagraphStyle(
                                    'ContentBoldStyle',
                                    parent=styles['Normal'],
                                    fontName=bold_font,
                                    fontSize=14,
                                    alignment=TA_JUSTIFY,
                                    leftIndent=0,
                                    spaceAfter=2,
                                    spaceBefore=0,
                                    leading=16.1
                                )
                                elements.append(Paragraph(sub_part, style))
                            else:
                                # Звичайний стиль для решти тексту
                                elements.append(Paragraph(sub_part, normal_justified_style))

    # Додаємо секцію про перетин кордону, якщо вона є (спрощено для прямого PDF)
    if border_crossing_data:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Перетин кордону України (ARKAN)", blue_header_style))
        elements.append(Paragraph("Дані додано до DOCX версії документа. Для повного відображення таблиць використовуйте DOCX або альтернативний метод PDF.", normal_justified_style))

    # Додаємо інформацію про ДМС, якщо вона є
    if dms_data:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("ІНФОРМАЦІЯ З ДМС", blue_header_style))
        elements.append(Paragraph("Дані ДМС додано до DOCX версії документа. Для повного відображення використовуйте DOCX або альтернативний метод PDF.", normal_justified_style))

    # Додаємо секцію нерухомості, якщо вона є
    if real_estate_data:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("НЕРУХОМІСТЬ", blue_header_style))
        elements.append(Paragraph("Дані про нерухомість додано до DOCX версії документа. Для повного відображення використовуйте DOCX або альтернативний метод PDF.", normal_justified_style))

    # Додаємо інформацію про родинні зв'язки, якщо вона є
    if family_data:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("РОДИННІ ЗВ'ЯЗКИ", blue_header_style))
        elements.append(Paragraph("Дані про родинні зв'язки додано до DOCX версії документа. Для повного відображення використовуйте DOCX або альтернативний метод PDF.", normal_justified_style))

    # Додаємо інформацію про транспортні засоби, якщо вона є
    if car_data:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("НАІС ТЗ", blue_header_style))
        elements.append(Paragraph(f"Знайдено транспортних засобів: {len(car_data)}. Для повного відображення даних про транспортні засоби використовуйте DOCX або альтернативний метод PDF.", normal_justified_style))

    # Будуємо PDF
    doc_template.build(elements)

    # Повертаємо байти PDF
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


def get_pdf_filename_from_intro(data: dict) -> str:
    """
    Витягує перше слово з блоку 'Початок документа' для формування імені PDF файлу.
    """
    content_list = data.get("Контент", [])

    for item in content_list:
        if item.get("header") == "Початок документа":
            content = item.get("content", "")
            # Витягуємо перше слово з контенту
            first_word = content.split()[0] if content.split() else "Dossier"
            # Прибираємо спеціальні символи з імені файлу
            import re
            first_word = re.sub(r'[^\w\s-]', '', first_word)
            return f"{first_word}.pdf"

    return "Dossier.pdf"