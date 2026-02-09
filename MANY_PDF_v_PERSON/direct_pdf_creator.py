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
    Форматирует текст с поддержкой различных стилей (жирный, курсив).
    """
    # Для упрощения, возвращаем текст как есть
    # В реальной реализации можно добавить поддержку тегов типа <b>, <i>
    return text


def create_pdf_directly(data: dict, photo_bytes: bytes = None, border_crossing_data: list = None, dms_data: dict = None, family_data: list = None, real_estate_data: list = None) -> bytes:
    """
    Создает PDF напрямую из данных, минуя DOCX.

    Args:
        data: Данные для генерации документа
        photo_bytes: Байты фото для вставки (опционально)

    Returns:
        bytes: Байты PDF-документа
    """
    # Регистрируем шрифты, поддерживающие кириллицу
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    from reportlab.pdfbase.ttfonts import TTFont

    # Попробуем использовать Liberation Serif (аналог Times New Roman с поддержкой кириллицы)
    try:
        # Зарегистрируем Liberation Serif как основной шрифт
        pdfmetrics.registerFont(TTFont('LiberationSerif', 'LiberationSerif-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('LiberationSerif-Bold', 'LiberationSerif-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('LiberationSerif-Italic', 'LiberationSerif-Italic.ttf'))
        pdfmetrics.registerFont(TTFont('LiberationSerif-BoldItalic', 'LiberationSerif-BoldItalic.ttf'))

        default_font = 'LiberationSerif'
        bold_font = 'LiberationSerif-Bold'
        italic_font = 'LiberationSerif-Italic'
        bold_italic_font = 'LiberationSerif-BoldItalic'
    except:
        # Если Liberation Serif недоступен, используем DejaVuSans
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSerif', 'DejaVuSerif.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSerif-Bold', 'DejaVuSerif-Bold.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSerif-Italic', 'DejaVuSerif-Italic.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSerif-BoldItalic', 'DejaVuSerif-BoldItalic.ttf'))

            default_font = 'DejaVuSerif'
            bold_font = 'DejaVuSerif-Bold'
            italic_font = 'DejaVuSerif-Italic'
            bold_italic_font = 'DejaVuSerif-BoldItalic'
        except:
            # Если и DejaVu недоступен, используем стандартный шрифт
            default_font = 'Helvetica'
            bold_font = 'Helvetica-Bold'
            italic_font = 'Helvetica-Oblique'
            bold_italic_font = 'Helvetica-BoldOblique'

    # Создаем PDF документ в памяти
    pdf_buffer = BytesIO()
    doc_template = SimpleDocTemplate(pdf_buffer, pagesize=A4, topMargin=56, bottomMargin=56,
                                     leftMargin=85, rightMargin=42)  # Конвертация из см в pt (1 см = 28.3 pt)

    # Рассчитываем ширину для таблиц на всю ширину страницы
    page_width = 595  # Ширина A4 в пунктах (8.27 дюймов * 72 pt/inch)
    left_margin = 85  # Левый отступ в пунктах
    right_margin = 42  # Правый отступ в пунктах
    full_width = page_width - left_margin - right_margin  # Ширина доступного пространства

    # Устанавливаем стили
    styles = getSampleStyleSheet()

    # Создаем кастомные стили
    title_center_style = ParagraphStyle(
        'TitleCenter',
        parent=styles['Normal'],
        fontName=default_font,
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=0,
        spaceBefore=0,
        leading=16.1  # 1,15 интервал
    )

    title_italic_style = ParagraphStyle(
        'TitleItalic',
        parent=styles['Normal'],
        fontName=italic_font,
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=0,
        spaceBefore=0,
        leading=16.1  # 1,15 интервал
    )

    blue_header_style = ParagraphStyle(
        'BlueHeader',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=14,
        alignment=TA_LEFT,
        textColor=colors.black,  # Изменяем цвет текста на черный
        backColor=colors.HexColor('#9BC2E6'),
        leftIndent=28,  # 7 пробелов (~7*4pt)
        spaceAfter=0,
        spaceBefore=0,
        leading=16.1  # 1,15 интервал
    )

    blue_header_italic_style = ParagraphStyle(
        'BlueHeaderItalic',
        parent=styles['Normal'],
        fontName=bold_italic_font,
        fontSize=14,
        alignment=TA_LEFT,
        textColor=colors.black,  # Изменяем цвет текста на черный
        backColor=colors.HexColor('#9BC2E6'),
        leftIndent=28,  # 7 пробелов (~7*4pt)
        spaceAfter=0,
        spaceBefore=0,
        leading=16.1  # 1,15 интервал
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
        leading=16.1  # 1,15 интервал
    )
    
    # Список элементов для построения PDF
    elements = []
    
    # Добавляем заголовки
    elements.append(Paragraph("АНАЛІТИЧНИЙ ПРОФІЛЬ", title_center_style))
    elements.append(Paragraph("на фізичну особу", title_center_style))
    elements.append(Spacer(1, 0))  # Пустая строка с высотой 8pt

    # 1. ЗАГАЛЬНИЙ ЗАГОЛОВОК ДОКУМЕНТА (Блакитна полоса)
    # Создаем таблицу для заголовка с блакитным фоном
    # Используем ширину всей страницы с учетом отступов
    full_width = 515  # Примерная ширина страницы A4 с отступами (595 - 2*40)
    header_table_data = [["       " + "АНКЕТНІ ДАНІ:"]]  # 7 пробелов перед заголовком

    header_table = Table(header_table_data, colWidths=[full_width])

    # Стиль таблицы с блакитным фоном
    header_table_style = TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), bold_italic_font),  # Жирный курсив
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGNMENT', (0, 0), (-1, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#9BC2E6')),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Убираем внутренние отступы, чтобы фон был под пробелами
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),  # Уменьшаем отступ сверху (примерно 1 мм)
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Увеличиваем отступ снизу (примерно 5 мм)
        # Полностью убираем границы
        ('LINEBELOW', (0, 0), (-1, -1), 0, colors.white),  # Прозрачная граница
        ('LINEABOVE', (0, 0), (-1, -1), 0, colors.white),
        ('LINEBEFORE', (0, 0), (-1, -1), 0, colors.white),
        ('LINEAFTER', (0, 0), (-1, -1), 0, colors.white),
    ])

    header_table.setStyle(header_table_style)
    elements.append(header_table)
    elements.append(Spacer(1, 8))  # Пустая строка высотой 8pt
    
    # Создаем таблицу для фото и вступительного текста
    content_list = data.get("Контент", [])
    intro_text = ""
    filtered_content = []
    
    for item in content_list:
        if item.get("header") == "Початок документа" and not intro_text:
            intro_text = item.get("content", "")
        else:
            filtered_content.append(item)
    
    # Создаем таблицу для фото и вступительного текста
    if photo_bytes or intro_text:
        # Подготовим элементы для таблицы
        photo_cell = []
        text_cell = []

        # Добавляем фото в левую ячейку
        if photo_bytes:
            try:
                # Создаем изображение из байтов
                img_buffer = BytesIO(photo_bytes)
                # Попробуем создать изображение с сохранением пропорций
                img = Image(img_buffer, width=142, height=142)  # 1.8 дюйма * 72 pt/inch
                img.hAlign = 'LEFT'  # Выравнивание изображения по левому краю
                photo_cell.append(img)
            except Exception as e:
                # Если не удалось добавить фото, выводим сообщение об ошибке в лог
                print(f"Ошибка при добавлении фото: {e}")
                # Вместо пустой ячейки добавим текстовое уведомление
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

        # Добавляем текст в правую ячейку
        if intro_text:
            # Очищаем текст от "д.н."
            intro_text = intro_text.replace("д.н.", "").replace("  ", " ")

            # Определяем специальные паттерны для "Місце народження" и "Громадянство"
            SPECIAL_PATTERN = r'([МM][іi][сc]ц[еe]\s*[нN][аa][рR][оO][дD][жJ][еЕ][нN]{2}[яY]\s*:|Громадянство\s*:)'

            # Разбиваем текст по ключевым словам и делаем их жирными
            BOLD_PATTERN = r'(Mарка\s*:|заявник\s*:|Марка\s*:|свідок\s*\(учасник\)\s*:|ухилянт\s*:|Вид\s*:|правопорушник\s*:|Номер\s*дозволу\s*:|телефони\s*:|[МM][іi][сc]ц[еe]\s*[нH][аa][рp][оo]др[еe][нH]{2}я\s*:|Громадянство\s*:|постраждалий\s*\(потерпілий\)\s*:|категорія\s*:|№\s+[А-ЯІЇ]{2,4}\s+\d+(?:\s+[А-ЯІЇ]{2}\s+\d+)?\s+від\s+\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}\s*,\s*орган:)'

            # Сначала разбиваем по специальным паттернам (Місце народження и Громадянство)
            special_parts = re.split(SPECIAL_PATTERN, intro_text)

            for special_part in special_parts:
                if not special_part:
                    continue

                # Проверяем, является ли часть специальным ключевым словом
                if re.fullmatch(SPECIAL_PATTERN, special_part):
                    # Жирный стиль для специальных ключевых слов
                    style = ParagraphStyle(
                        'IntroSpecialBoldStyle',
                        parent=styles['Normal'],
                        fontName=bold_font,
                        fontSize=14,
                        alignment=TA_LEFT,  # Для вступительного текста используем левое выравнивание
                        leftIndent=0,
                        spaceAfter=2,
                        spaceBefore=6,  # Добавляем отступ сверху для новой строки
                        leading=16.1
                    )
                    text_cell.append(Paragraph(special_part, style))
                else:
                    # Разбиваем оставшийся текст по обычным ключевым словам
                    parts = re.split(BOLD_PATTERN, special_part)

                    for part in parts:
                        if not part:
                            continue

                        # Проверяем, является ли часть ключевым словом
                        if re.fullmatch(BOLD_PATTERN, part):
                            # Жирный стиль для ключевых слов
                            style = ParagraphStyle(
                                'IntroBoldStyle',
                                parent=styles['Normal'],
                                fontName=bold_font,
                                fontSize=14,
                                alignment=TA_LEFT,  # Для вступительного текста используем левое выравнивание
                                leftIndent=0,
                                spaceAfter=2,
                                spaceBefore=0,
                                leading=16.1
                            )
                            text_cell.append(Paragraph(part, style))
                        else:
                            # Обычный стиль для остального текста
                            style = ParagraphStyle(
                                'IntroNormalStyle',
                                parent=styles['Normal'],
                                fontName=default_font,
                                fontSize=14,
                                alignment=TA_LEFT,  # Для вступительного текста используем левое выравнивание
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

        # Создаем таблицу с двумя колонками
        # 142 pt - ширина фото (1.8 дюйма), 28 pt - отступ 5 мм (5/25.4*72), 318-28=290 pt - ширина текста
        table_data = [[photo_cell, text_cell]]
        table = Table(table_data, colWidths=[142, 290])  # 1.8 дюйма * 72 = 142 pt, остаток с учетом отступа

        # Стиль таблицы
        table_style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (0, -1), 4),      # Левый отступ для фото
            ('RIGHTPADDING', (0, 0), (0, -1), 14),    # Правый отступ для фото (примерно 5 мм)
            ('LEFTPADDING', (1, 0), (1, -1), 14),     # Левый отступ для текста (примерно 5 мм)
            ('RIGHTPADDING', (1, 0), (1, -1), 4),     # Правый отступ для текста
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ])

        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 6))  # Отступ после таблицы

    # Обрабатываем остальные блоки
    for item in filtered_content:
        header = item.get("header", "").strip()
        content = item.get("content", "").strip()

        if header:
            # Создаем таблицу для заголовка с блакитным фоном на всю ширину
            header_table_data = [["       " + header.upper()]]  # 7 пробелов перед заголовком
            header_table = Table(header_table_data, colWidths=[full_width])  # Используем ту же ширину

            # Стиль таблицы с блакитным фоном
            header_table_style = TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), bold_italic_font),  # Жирный курсив
                ('FONTSIZE', (0, 0), (-1, -1), 14),
                ('ALIGNMENT', (0, 0), (-1, -1), 'LEFT'),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#9BC2E6')),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Убираем внутренние отступы
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 2),  # Уменьшаем отступ сверху (примерно 1 мм)
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Увеличиваем отступ снизу (примерно 5 мм)
                # Полностью убираем границы
                ('LINEBELOW', (0, 0), (-1, -1), 0, colors.white),  # Прозрачная граница
                ('LINEABOVE', (0, 0), (-1, -1), 0, colors.white),
                ('LINEBEFORE', (0, 0), (-1, -1), 0, colors.white),
                ('LINEAFTER', (0, 0), (-1, -1), 0, colors.white),
            ])

            header_table.setStyle(header_table_style)
            elements.append(header_table)

            if content:
                # Разбиваем контент по абзацам
                paragraphs_list = content.split('\n')

                # Определяем паттерн для конкретного заголовка
                if header == "ЄРДР":
                    pat = r'(№\s+\d{24}\s+від\s+\d{2}\.\d{2}\.\d{4}\s*,\s*за\s*СТ\.|' + BOLD_PATTERN[1:]  # Убираем первую скобку
                elif header == "Адреса":
                    pat = r'(місце\s*проживання\s*:|' + BOLD_PATTERN[1:]  # Убираем первую скобку
                else:
                    pat = BOLD_PATTERN

                for p_text in paragraphs_list:
                    if p_text.strip():
                        # Применяем стиль с выравниванием по ширине
                        # Разбиваем текст по ключевым словам
                        sub_parts = re.split(pat, p_text)
                        for sub_part in sub_parts:
                            if not sub_part:
                                continue

                            # Проверяем, является ли часть ключевым словом
                            if re.fullmatch(pat, sub_part):
                                # Жирный стиль для ключевых слов
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
                                # Обычный стиль для остального текста
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

    # Строим PDF
    doc_template.build(elements)

    # Возвращаем байты PDF
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


def get_pdf_filename_from_intro(data: dict) -> str:
    """
    Извлекает первое слово из блока 'Початок документа' для формирования имени PDF файла.
    """
    content_list = data.get("Контент", [])

    for item in content_list:
        if item.get("header") == "Початок документа":
            content = item.get("content", "")
            # Извлекаем первое слово из контента
            first_word = content.split()[0] if content.split() else "Dossier"
            # Убираем специальные символы из имени файла
            import re
            first_word = re.sub(r'[^\w\s-]', '', first_word)
            return f"{first_word}.pdf"

    return "Dossier.pdf"