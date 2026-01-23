from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from PIL import Image
import io
import os


import re

def generate_docx(data: dict, photo_bytes: bytes = None) -> bytes:
    """
    Генерує документ Word з вибраних абзаців.
    """
    doc = Document()
    
    # Налаштування полів сторінки
    section = doc.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(3)
    section.right_margin = Cm(1.5)
    
    # Налаштування стилів
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(14)

    BOLD_PATTERN = r'(Mарка\s*:|заявник\s*:|Марка\s*:|свідок\s*\(учасник\)\s*:|ухилянт\s*:|Вид\s*:|правопорушник\s*:|Номер\s*дозволу\s*:|телефони\s*:|[МM][іi][сc]ц[еe]\s*[нH][аa][рp][оo]дж[еe][нH]{2}я\s*:|Громадянство\s*:|постраждалий\s*\(потерпілий\)\s*:|категорія\s*:|№\s+[А-ЯІЇ]{2,4}\s+\d+(?:\s+[А-ЯІЇ]{2}\s+\d+)?\s+від\s+\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2}\s*,\s*орган:)'

    def add_bulleted_content(container, text, alignment=None, use_bullet_style=True, bold_matches=True, bold_content=False, pattern=BOLD_PATTERN):
        """Разбивает текст по шаблону и создает маркированный список для ключевых слов."""
        if pattern:
            parts = re.split(pattern, text)
            current_p = None
            
            for part in parts:
                if not part:
                    continue
                
                # Проверяем, является ли часть ключевым словом
                if re.fullmatch(pattern, part):
                    # Начинаем новый абзац (маркированный или обычный)
                    style = 'List Bullet' if use_bullet_style else None
                    current_p = container.add_paragraph(style=style)
                    current_p.paragraph_format.space_before = Pt(0)
                    current_p.paragraph_format.space_after = Pt(2)
                    if alignment is not None:
                        current_p.alignment = alignment
                    
                    run = current_p.add_run(part)
                    run.bold = bold_matches
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(14)
                else:
                    if current_p is None:
                        # Если ключевых слов еще не было, создаем обычный абзац
                        current_p = container.add_paragraph()
                        current_p.paragraph_format.space_before = Pt(0)
                        current_p.paragraph_format.space_after = Pt(2)
                        if alignment is not None:
                            current_p.alignment = alignment
                    
                    run = current_p.add_run(part)
                    run.bold = bold_content
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(14)
        else:
            # Просто добавляем текст как обычный
            current_p = container.add_paragraph()
            current_p.paragraph_format.space_before = Pt(0)
            current_p.paragraph_format.space_after = Pt(2)
            if alignment is not None:
                current_p.alignment = alignment
            run = current_p.add_run(text)
            run.bold = bold_content
            run.font.name = 'Times New Roman'
            run.font.size = Pt(14)
    
    # 1. ЗАГАЛЬНИЙ ЗАГОЛОВОК ДОКУМЕНТА (Блакитна полоса)
    t_top = doc.add_table(rows=1, cols=1)
    t_top.width = Inches(6.5)
    cell_top = t_top.rows[0].cells[0]
    
    # Блакитний фон
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), '9BC2E6')
    cell_top._element.get_or_add_tcPr().append(shd)
    
    p_top = cell_top.paragraphs[0]
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.paragraph_format.space_before = Pt(0)
    p_top.paragraph_format.space_after = Pt(0)
    run_top = p_top.add_run("АНАЛІТИЧНЕ ДОСЬЄ НА ОСОБУ")
    run_top.bold = True
    run_top.font.size = Pt(14)
    doc.add_paragraph() # Відступ повернуто
    
    # Шукаємо вступний текст (Початок документа)
    content_list = data.get("Контент", [])
    intro_text = ""
    filtered_content = []
    
    for item in content_list:
        if item.get("header") == "Початок документа" and not intro_text:
            intro_text = item.get("content", "")
        else:
            filtered_content.append(item)
    
    # Створюємо таблицю для розміщення фото та вступного тексту
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    
    # Додаємо фото в ліву клітинку
    left_cell = table.rows[0].cells[0]
    if photo_bytes:
        paragraph = left_cell.paragraphs[0]
        run = paragraph.add_run()
        run.add_picture(BytesIO(photo_bytes), width=Inches(1.8))
    elif os.path.exists('default_avatar.png'):
        paragraph = left_cell.paragraphs[0]
        run = paragraph.add_run()
        run.add_picture('default_avatar.png', width=Inches(1.8))
    
    # Встановлюємо ширину колонок через клітинки
    left_cell.width = Inches(2.0)
    right_cell = table.rows[0].cells[1]
    right_cell.width = Inches(4.5)
    right_cell.vertical_alignment = 1
    
    
    # Використовуємо універсальну функцію форматування для всього тексту в клітинці
    if intro_text:
        # Видаляємо порожній параграф, який створюється автоматично
        if len(right_cell.paragraphs) > 0 and not right_cell.paragraphs[0].text.strip():
             p = right_cell.paragraphs[0]
             p._element.getparent().remove(p._element)
             
        # Очищаем текст от "д.н."
        intro_text = intro_text.replace("д.н.", "").replace("  ", " ")
        
        # Инвертированное жирное выделение для первого блока:
        # Ключевые слова (bold_matches=False) - обычные
        # Контент (bold_content=True) - жирный
        add_bulleted_content(right_cell, intro_text, alignment=WD_ALIGN_PARAGRAPH.LEFT, 
                             use_bullet_style=False, bold_matches=False, bold_content=True, pattern=None)
    else:
        title_paragraph = right_cell.paragraphs[0]
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        title_run = title_paragraph.add_run("Особисте досьє")
        title_run.font.size = Pt(14)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(0, 0, 0)
    
    

    # Добавляем контент (вже відфільтрований без вступу)
    for item in filtered_content:
        header = item.get("header", "").strip()
        content = item.get("content", "").strip()
        
        if header:
            if header == "Початок документа":
                # Виводимо тільки контент як звичайний текст на початку
                if content:
                    add_bulleted_content(doc, content, pattern=None)
                    # Добавляем отступ после вводного блока
                    doc.add_paragraph().paragraph_format.space_after = Pt(6)
                continue
            
            # Створюємо таблицю для заголовка на блакитному фоні
            t = doc.add_table(rows=1, cols=1)
            t.width = Inches(6.5)
            cell = t.rows[0].cells[0]
            
            # Налаштування блакитного фону (#9BC2E6)
            from docx.oxml.ns import qn
            from docx.oxml import OxmlElement
            shading_elm = OxmlElement('w:shd')
            shading_elm.set(qn('w:fill'), '9BC2E6') 
            cell._element.get_or_add_tcPr().append(shading_elm)
            
            # Прибираємо границі
            tcPr = cell._element.get_or_add_tcPr()
            tcBorders = OxmlElement('w:tcBorders')
            for border in ['top', 'left', 'bottom', 'right']:
                b = OxmlElement(f'w:{border}')
                b.set(qn('w:val'), 'none')
                tcBorders.append(b)
            tcPr.append(tcBorders)
            
            p_h = cell.paragraphs[0]
            p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run_h = p_h.add_run(header)
            run_h.bold = True
            run_h.font.size = Pt(12)
            p_h.paragraph_format.space_before = Pt(0)
            p_h.paragraph_format.space_after = Pt(0)
        
            paragraphs_list = content.split('\n')
            for i, p_text in enumerate(paragraphs_list):
                if p_text.strip():
                    # Применяем выравнивание по центру для всех блоков кроме "Початок документа"
                    pat = r'(місце\s*проживання\s*:|' + BOLD_PATTERN[1:] if header == "Адреса" else BOLD_PATTERN
                    p_c = add_bulleted_content(doc, p_text.strip(), alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, pattern=pat)
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


