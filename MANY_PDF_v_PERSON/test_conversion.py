"""
Тестовый скрипт для проверки конвертации DOCX в PDF
"""
import os
import tempfile
from document_generator import generate_docx
from docx_to_pdf_converter import convert_docx_to_pdf

def test_conversion():
    # Подготовим тестовые данные
    test_data = {
        "Контент": [
            {
                "header": "Початок документа",
                "content": "Іванов Іван Іванович д.н. 12.05.1985 Марка: BMW X5 заявник: Петров Петро Петрович"
            },
            {
                "header": "Адреса",
                "content": "м. Київ, вул. Хрещатик, 1"
            },
            {
                "header": "Контакти",
                "content": "телефони: +380 12 345 67 89"
            }
        ]
    }

    print("Генерация DOCX...")
    docx_bytes = generate_docx(test_data)
    print(f"DOCX успешно создан, размер: {len(docx_bytes)} байт")

    print("Конвертация в PDF...")
    pdf_bytes = convert_docx_to_pdf(docx_bytes)
    print(f"PDF успешно создан, размер: {len(pdf_bytes)} байт")

    # Сохраняем файлы для проверки
    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as docx_file:
        docx_file.write(docx_bytes)
        docx_filename = docx_file.name

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as pdf_file:
        pdf_file.write(pdf_bytes)
        pdf_filename = pdf_file.name

    print(f"Файлы сохранены:")
    print(f"  DOCX: {docx_filename}")
    print(f"  PDF: {pdf_filename}")

    # Проверяем, что файлы не пустые
    assert os.path.getsize(docx_filename) > 0, "DOCX файл пустой"
    assert os.path.getsize(pdf_filename) > 0, "PDF файл пустой"

    # Проверим, что PDF содержит ожидаемые элементы
    # (проверим, что это действительно PDF файл)
    with open(pdf_filename, 'rb') as f:
        pdf_header = f.read(8)
        assert pdf_header.startswith(b'%PDF-'), "Файл не является PDF"

    print("PDF файл корректно сгенерирован!")

    print("Тест пройден успешно!")

if __name__ == "__main__":
    test_conversion()