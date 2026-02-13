"""
Модуль для поиска изображений автомобилей по цвету и марке/модели
"""

import requests
import os
from typing import Optional, Tuple
from PIL import Image
from io import BytesIO
from ddgs import DDGS


def search_car_image_by_attributes(brand: str = "", model: str = "", color: str = "", year: str = "") -> Optional[bytes]:
    """
    Ищет изображение автомобиля по марке, модели, цвету и году выпуска

    Args:
        brand: Марка автомобиля
        model: Модель автомобиля
        color: Цвет автомобиля
        year: Год выпуска автомобиля

    Returns:
        bytes: Изображение в байтах или None если не найдено
    """

    search_terms = []
    if brand:
        search_terms.append(brand)
    if model:
        search_terms.append(model)
    if color:
        search_terms.append(color)
    if year:
        search_terms.append(year)

    if not search_terms:
        return None

    search_query = " ".join(search_terms) + " car photo"

    try:
        # Используем DuckDuckGo Search
        ddgs = DDGS()
        results = ddgs.images(
            search_query,
            max_results=1
        )

        if results:
            image_url = results[0].get('image')
            if image_url:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                img_response = requests.get(image_url, headers=headers)
                if img_response.status_code == 200:
                    return img_response.content
    except Exception as e:
        print(f"Ошибка при поиске изображения через DuckDuckGo: {e}")

    # Если ничего не нашли, возвращаем None
    return None


def download_and_resize_image(image_bytes: bytes, size: Tuple[int, int] = (400, 300)) -> Optional[bytes]:
    """
    Загружает изображение, изменяет его размер и возвращает в байтах
    
    Args:
        image_bytes: Исходное изображение в байтах
        size: Желаемый размер (ширина, высота)
    
    Returns:
        bytes: Измененное изображение в байтах или None при ошибке
    """
    try:
        image = Image.open(BytesIO(image_bytes))
        
        # Если изображение в режиме RGBA (есть альфа-канал), конвертируем в RGB
        if image.mode == 'RGBA':
            # Создаем белый фон
            background = Image.new('RGB', image.size, (255, 255, 255))
            # Накладываем изображение на белый фон
            background.paste(image, mask=image.split()[-1])  # Используем альфа-канал как маску
            image = background
        elif image.mode != 'RGB':
            # Для других режимов конвертируем в RGB
            image = image.convert('RGB')
        
        # Изменяем размер изображения
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Сохраняем обратно в байты
        output = BytesIO()
        image.save(output, format='JPEG', quality=85)
        output.seek(0)
        
        return output.getvalue()
    except Exception as e:
        print(f"Ошибка при изменении размера изображения: {e}")
        return None


def get_car_image(brand: str = "", model: str = "", color: str = "", year: str = "") -> Optional[bytes]:
    """
    Основная функция для получения изображения автомобиля по характеристикам

    Args:
        brand: Марка автомобиля
        model: Модель автомобиля
        color: Цвет автомобиля
        year: Год выпуска автомобиля

    Returns:
        bytes: Изображение автомобиля в байтах или None если не найдено
    """
    # Попробуем найти изображение
    image_bytes = search_car_image_by_attributes(brand, model, color, year)

    if image_bytes:
        # Изменим размер изображения для использования в документе
        resized_image = download_and_resize_image(image_bytes, (200, 150))
        return resized_image

    return None