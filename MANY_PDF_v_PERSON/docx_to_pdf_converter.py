import io
import tempfile
import os
from docxtopdf import convert


def convert_docx_to_pdf(docx_bytes: bytes) -> bytes:
    """
    Конвертирует DOCX-документ в PDF.

    Args:
        docx_bytes: Байты DOCX-документа

    Returns:
        bytes: Байты PDF-документа
    """
    # Создаем временные файлы
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as docx_file:
        docx_file.write(docx_bytes)
        docx_filename = docx_file.name

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_file:
        pdf_filename = pdf_file.name

    try:
        # Конвертируем DOCX в PDF
        convert(docx_filename, pdf_filename)

        # Читаем результат
        with open(pdf_filename, 'rb') as f:
            pdf_bytes = f.read()

        return pdf_bytes
    finally:
        # Удаляем временные файлы
        if os.path.exists(docx_filename):
            os.remove(docx_filename)
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)


def get_pdf_filename_from_docx(docx_filename: str) -> str:
    """
    Генерирует имя PDF-файла из имени DOCX-файла.

    Args:
        docx_filename: Имя DOCX-файла

    Returns:
        str: Имя PDF-файла
    """
    if docx_filename.lower().endswith('.docx'):
        return docx_filename[:-5] + '.pdf'
    else:
        return docx_filename + '.pdf'