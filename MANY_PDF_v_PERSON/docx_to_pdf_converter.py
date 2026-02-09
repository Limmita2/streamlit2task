import io
import tempfile
import os
from docxtopdf import convert


def convert_docx_to_pdf(docx_bytes: bytes) -> bytes:
    """
    Конвертує DOCX-документ в PDF.

    Args:
        docx_bytes: Байти DOCX-документа

    Returns:
        bytes: Байти PDF-документа
    """
    # Спробуємо спочатку використати docxtopdf
    try:
        # Створюємо тимчасові файли
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as docx_file:
            docx_file.write(docx_bytes)
            docx_filename = docx_file.name

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_file:
            pdf_filename = pdf_file.name

        try:
            # Конвертируем DOCX в PDF
            convert(docx_filename, pdf_filename)

            # Читаємо результат
            with open(pdf_filename, 'rb') as f:
                pdf_bytes = f.read()

            # Перевіряємо, що PDF не пустий
            if len(pdf_bytes) > 0:
                return pdf_bytes
            else:
                # Якщо docxtopdf повернув пустий PDF, використовуємо альтернативний метод
                raise Exception("docxtopdf returned empty PDF")
        finally:
            # Видаляємо тимчасові файли
            if os.path.exists(docx_filename):
                os.remove(docx_filename)
            if os.path.exists(pdf_filename):
                os.remove(pdf_filename)
    except Exception as e:
        # Якщо docxtopdf не працює, використовуємо альтернативний метод
        from docx_to_pdf_converter_alt import convert_docx_to_pdf as alt_convert
        return alt_convert(docx_bytes)


def get_pdf_filename_from_docx(docx_filename: str) -> str:
    """
    Генерує ім'я PDF-файлу з імені DOCX-файлу.

    Args:
        docx_filename: Ім'я DOCX-файлу

    Returns:
        str: Ім'я PDF-файлу
    """
    if docx_filename.lower().endswith('.docx'):
        return docx_filename[:-5] + '.pdf'
    else:
        return docx_filename + '.pdf'