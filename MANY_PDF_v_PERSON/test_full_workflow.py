"""
Тестовый скрипт для проверки работы приложения с новой библиотекой
"""
import os
import tempfile
from document_generator import generate_docx
from docx_to_pdf_converter import convert_docx_to_pdf

def test_full_workflow():
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

    print("Тестирование полного рабочего процесса...")
    print("Генерация DOCX...")
    docx_bytes = generate_docx(test_data)
    print(f"DOCX успешно создан, размер: {len(docx_bytes)} байт")

    print("Конвертация в PDF с помощью docxtopdf...")
    pdf_bytes = convert_docx_to_pdf(docx_bytes)
    print(f"PDF успешно создан, размер: {len(pdf_bytes)} байт")

    # Проверим, что PDF содержит ожидаемые элементы
    # (проверим, что это действительно PDF файл)
    pdf_header = pdf_bytes[:8]
    assert pdf_header.startswith(b'%PDF-'), "Файл не является PDF"

    print("PDF файл корректно сгенерирован!")
    
    # Сохраняем файлы для ручной проверки
    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as docx_file:
        docx_file.write(docx_bytes)
        docx_path = docx_file.name
        print(f"DOCX файл сохранен: {docx_path}")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as pdf_file:
        pdf_file.write(pdf_bytes)
        pdf_path = pdf_file.name
        print(f"PDF файл сохранен: {pdf_path}")

    print("Тест пройден успешно!")

if __name__ == "__main__":
    test_full_workflow()