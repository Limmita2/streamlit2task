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
    # Попробуем сначала использовать docxtopdf
    try:
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

            # Проверяем, что PDF не пустой
            if len(pdf_bytes) > 0:
                return pdf_bytes
            else:
                # Если docxtopdf вернул пустой PDF, используем альтернативный метод
                raise Exception("docxtopdf returned empty PDF")
        finally:
            # Удаляем временные файлы
            if os.path.exists(docx_filename):
                os.remove(docx_filename)
            if os.path.exists(pdf_filename):
                os.remove(pdf_filename)
    except Exception as e:
        # Если docxtopdf не работает, используем альтернативный метод
        from docx_to_pdf_converter_alt import convert_docx_to_pdf as alt_convert
        return alt_convert(docx_bytes)


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