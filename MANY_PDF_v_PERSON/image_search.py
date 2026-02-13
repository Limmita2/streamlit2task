# """
# Модуль для поиска изображений автомобилей по цвету и марке/модели
# """

# import requests
# import os
# from typing import Optional, Tuple
# from PIL import Image
# from io import BytesIO
# from ddgs import DDGS


# def search_car_image_by_attributes(brand: str = "", model: str = "", color: str = "", year: str = "") -> Optional[bytes]:
#     """
#     Ищет изображение автомобиля по марке, модели, цвету и году выпуска

#     Args:
#         brand: Марка автомобиля
#         model: Модель автомобиля
#         color: Цвет автомобиля
#         year: Год выпуска автомобиля

#     Returns:
#         bytes: Изображение в байтах или None если не найдено
#     """

#     search_terms = []
#     if brand:
#         search_terms.append(brand)
#     if model:
#         search_terms.append(model)
#     if color:
#         search_terms.append(color)
#     if year:
#         search_terms.append(year)

#     if not search_terms:
#         return None

#     search_query = " ".join(search_terms) + " car photo"

#     try:
#         # Используем DuckDuckGo Search
#         ddgs = DDGS()
#         results = ddgs.images(
#             search_query,
#             max_results=1
#         )

#         if results:
#             image_url = results[0].get('image')
#             if image_url:
#                 headers = {
#                     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#                 }
#                 img_response = requests.get(image_url, headers=headers)
#                 if img_response.status_code == 200:
#                     return img_response.content
#     except Exception as e:
#         print(f"Ошибка при поиске изображения через DuckDuckGo: {e}")

#     # Если ничего не нашли, возвращаем None
#     return None


# def download_and_resize_image(image_bytes: bytes, size: Tuple[int, int] = (400, 300)) -> Optional[bytes]:
#     """
#     Загружает изображение, изменяет его размер и возвращает в байтах
    
#     Args:
#         image_bytes: Исходное изображение в байтах
#         size: Желаемый размер (ширина, высота)
    
#     Returns:
#         bytes: Измененное изображение в байтах или None при ошибке
#     """
#     try:
#         image = Image.open(BytesIO(image_bytes))
        
#         # Если изображение в режиме RGBA (есть альфа-канал), конвертируем в RGB
#         if image.mode == 'RGBA':
#             # Создаем белый фон
#             background = Image.new('RGB', image.size, (255, 255, 255))
#             # Накладываем изображение на белый фон
#             background.paste(image, mask=image.split()[-1])  # Используем альфа-канал как маску
#             image = background
#         elif image.mode != 'RGB':
#             # Для других режимов конвертируем в RGB
#             image = image.convert('RGB')
        
#         # Изменяем размер изображения
#         image.thumbnail(size, Image.Resampling.LANCZOS)
        
#         # Сохраняем обратно в байты
#         output = BytesIO()
#         image.save(output, format='JPEG', quality=85)
#         output.seek(0)
        
#         return output.getvalue()
#     except Exception as e:
#         print(f"Ошибка при изменении размера изображения: {e}")
#         return None


# def get_car_image(brand: str = "", model: str = "", color: str = "", year: str = "") -> Optional[bytes]:
#     """
#     Основная функция для получения изображения автомобиля по характеристикам

#     Args:
#         brand: Марка автомобиля
#         model: Модель автомобиля
#         color: Цвет автомобиля
#         year: Год выпуска автомобиля

#     Returns:
#         bytes: Изображение автомобиля в байтах или None если не найдено
#     """
#     # Попробуем найти изображение
#     image_bytes = search_car_image_by_attributes(brand, model, color, year)

#     if image_bytes:
#         # Изменим размер изображения для использования в документе
#         resized_image = download_and_resize_image(image_bytes, (200, 150))
#         return resized_image

#     # Если изображение не найдено, возвращаем заглушку
#     try:
#         # Попробуем использовать изображение заглушки по умолчанию для автомобилей
#         default_car_image_path = 'default_avto.jpg'
        
#         # Проверим, существует ли файл заглушки для автомобилей
#         if os.path.exists(default_car_image_path):
#             with open(default_car_image_path, 'rb') as f:
#                 default_img_bytes = f.read()
                
#                 # Изменим размер изображения заглушки
#                 output = BytesIO()
#                 image = Image.open(BytesIO(default_img_bytes))
                
#                 # Если изображение в режиме RGBA (есть альфа-канал), конвертируем в RGB
#                 if image.mode == 'RGBA':
#                     # Создаем белый фон
#                     background = Image.new('RGB', image.size, (255, 255, 255))
#                     # Накладываем изображение на белый фон
#                     background.paste(image, mask=image.split()[-1])  # Используем альфа-канал как маску
#                     image = background
#                 elif image.mode != 'RGB':
#                     # Для других режимов конвертируем в RGB
#                     image = image.convert('RGB')

#                 # Изменяем размер изображения
#                 image.thumbnail((200, 150), Image.Resampling.LANCZOS)

#                 # Сохраняем обратно в байты
#                 image.save(output, format='JPEG', quality=85)
#                 output.seek(0)

#                 return output.getvalue()
#         else:
#             # Если файла заглушки для автомобилей нет, используем заглушку по умолчанию
#             if os.path.exists('default_avatar.png'):
#                 with open('default_avatar.png', 'rb') as f:
#                     default_img_bytes = f.read()
                    
#                     # Изменим размер изображения заглушки
#                     output = BytesIO()
#                     image = Image.open(BytesIO(default_img_bytes))
                    
#                     # Если изображение в режиме RGBA (есть альфа-канал), конвертируем в RGB
#                     if image.mode == 'RGBA':
#                         # Создаем белый фон
#                         background = Image.new('RGB', image.size, (255, 255, 255))
#                         # Накладываем изображение на белый фон
#                         background.paste(image, mask=image.split()[-1])  # Используем альфа-канал как маску
#                         image = background
#                     elif image.mode != 'RGB':
#                         # Для других режимов конвертируем в RGB
#                         image = image.convert('RGB')

#                     # Изменяем размер изображения
#                     image.thumbnail((200, 150), Image.Resampling.LANCZOS)

#                     # Сохраняем обратно в байты
#                     image.save(output, format='JPEG', quality=85)
#                     output.seek(0)

#                     return output.getvalue()
#     except Exception as e:
#         print(f"Ошибка при использовании заглушки: {e}")
    
#     return None

"""
Модуль для поиска изображений автомобилей по цвету и марке/модели
Улучшенная версия: каскадный поиск + перевод на английский
"""

import requests
import os
from typing import Optional, Tuple, List
from PIL import Image
from io import BytesIO
from ddgs import DDGS

# Словарь для быстрого перевода популярных марок и цветов на английский
# Это критически важно, так как DuckDuckGo лучше ищет на английском
TRANSLATION_MAP = {
    # Марки
    'бмв': 'BMW', 'bmw': 'BMW',
    'мерседес': 'Mercedes', 'mercedes': 'Mercedes',
    'ауди': 'Audi', 'audi': 'Audi',
    'тойота': 'Toyota', 'toyota': 'Toyota',
    'ниссан': 'Nissan', 'nissan': 'Nissan',
    'хендай': 'Hyundai', 'hyundai': 'Hyundai',
    'киа': 'Kia', 'kia': 'Kia',
    'лексус': 'Lexus', 'lexus': 'Lexus',
    'фольксваген': 'Volkswagen', 'volkswagen': 'Volkswagen',
    'вольво': 'Volvo', 'volvo': 'Volvo',
    'порше': 'Porsche', 'porsche': 'Porsche',
    'лада': 'Lada', 'lada': 'Lada',
    'шевроле': 'Chevrolet', 'chevrolet': 'Chevrolet',
    'форд': 'Ford', 'ford': 'Ford',
    'рено': 'Renault', 'renault': 'Renault',
    # Цвета
    'черный': 'black', 'чёрный': 'black', 'black': 'black',
    'белый': 'white', 'white': 'white',
    'серый': 'gray', 'grey': 'gray',
    'серебристый': 'silver', 'silver': 'silver',
    'красный': 'red', 'red': 'red',
    'синий': 'blue', 'blue': 'blue',
    'зеленый': 'green', 'green': 'green',
    'желтый': 'yellow', 'yellow': 'yellow',
    'коричневый': 'brown', 'brown': 'brown',
    'бежевый': 'beige', 'beige': 'beige',
    'оранжевый': 'orange', 'orange': 'orange',
}

def _translate_keyword(keyword: str) -> str:
    """Переводит ключевое слово на английский через словарь, если есть."""
    return TRANSLATION_MAP.get(keyword.lower(), keyword)

def _generate_search_queries(brand: str, model: str, color: str, year: str) -> List[str]:
    """
    Генерирует список запросов от самого точного к более общим.
    Это помогает найти фото, даже если точного сочетания "цвет+год" нет.
    """
    # Переводим параметры
    b = _translate_keyword(brand)
    m = model  # Модель обычно совпадает (X5, Camry), перевод не всегда нужен
    c = _translate_keyword(color)
    
    queries = []
    
    # 1. Самый точный: "Марка Модель Цвет Год"
    if b and m and c and year:
        queries.append(f"{b} {m} {c} {year} car exterior")
    
    # 2. Без года (год часто мешает, фото могут быть свежее или старее)
    if b and m and c:
        queries.append(f"{b} {m} {c} car")
        
    # 3. Без цвета (если цвет редкий, лучше просто найти модель)
    if b and m and year:
        queries.append(f"{b} {m} {year} car")
        
    # 4. Самый простой: просто Марка Модель
    if b and m:
        queries.append(f"{b} {m} car")

    # Убираем дубликаты, если параметры совпадали
    return list(dict.fromkeys(queries))

def search_car_image_by_attributes(brand: str = "", model: str = "", color: str = "", year: str = "") -> Optional[bytes]:
    """
    Ищет изображение автомобиля, перебирая разные комбинации запросов.
    """
    queries = _generate_search_queries(brand, model, color, year)
    
    if not queries:
        return None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }

    try:
        # Используем контекстный менеджер для DDGS
        with DDGS() as ddgs:
            for query in queries:
                print(f"Пробуем запрос: {query}") # Для отладки
                try:
                    # Ищем до 5 результатов, потому что первые могут быть некачественными
                    results = ddgs.images(query, max_results=5)
                    
                    if not results:
                        continue # Если ничего нет по этому запросу, идем к следующему

                    for res in results:
                        image_url = res.get('image')
                        if not image_url:
                            continue
                            
                        try:
                            # Таймаут важен, чтобы не зависать на битых ссылках
                            img_response = requests.get(image_url, headers=headers, timeout=5)
                            
                            # Проверяем, что это реально картинка, а не HTML страница
                            content_type = img_response.headers.get('Content-Type', '')
                            if img_response.status_code == 200 and 'image' in content_type:
                                # Проверяем размер, чтобы не вернуть пустую пикчу 1x1
                                if len(img_response.content) > 2048: 
                                    return img_response.content
                        except Exception:
                            continue # Ошибка скачивания конкретной картинки, идем к следующей
                            
                except Exception as e:
                    print(f"Ошибка поиска по запросу '{query}': {e}")
                    continue

    except Exception as e:
        print(f"Критическая ошибка DuckDuckGo: {e}")

    return None

def download_and_resize_image(image_bytes: bytes, size: Tuple[int, int] = (400, 300)) -> Optional[bytes]:
    """
    Загружает изображение, изменяет его размер и возвращает в байтах.
    Добавлена обработка палитры (P mode) и прозрачности.
    """
    try:
        image = Image.open(BytesIO(image_bytes))
        
        # Конвертируем в RGB, обрабатывая разные режимы (RGBA, P, L и т.д.)
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        elif image.mode == 'P':
            # Палитровые изображения лучше конвертировать через RGBA чтобы не терять прозрачность если она есть,
            # либо сразу в RGB
            image = image.convert('RGB')
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Изменяем размер
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        output = BytesIO()
        image.save(output, format='JPEG', quality=85)
        output.seek(0)
        
        return output.getvalue()
    except Exception as e:
        print(f"Ошибка при изменении размера изображения: {e}")
        return None

def get_car_image(brand: str = "", model: str = "", color: str = "", year: str = "") -> Optional[bytes]:
    """
    Основная функция. Сначала пытаемся найти в сети, потом отдаем заглушку.
    """
    image_bytes = search_car_image_by_attributes(brand, model, color, year)

    if image_bytes:
        resized_image = download_and_resize_image(image_bytes, (200, 150))
        return resized_image

    # Логика заглушки (оставлена без изменений из вашего кода)
    try:
        default_car_image_path = 'default_avto.jpg'
        if os.path.exists(default_car_image_path):
            with open(default_car_image_path, 'rb') as f:
                default_img_bytes = f.read()
                resized_image = download_and_resize_image(default_img_bytes, (200, 150))
                if resized_image:
                    return resized_image
        
        if os.path.exists('default_avatar.png'):
            with open('default_avatar.png', 'rb') as f:
                default_img_bytes = f.read()
                resized_image = download_and_resize_image(default_img_bytes, (200, 150))
                if resized_image:
                    return resized_image
    except Exception as e:
        print(f"Ошибка при использовании заглушки: {e}")
    
    return None