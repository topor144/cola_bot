import asyncio
import sys
import os

# Добавляем родительскую директорию в путь импорта
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.ocr_parser import perform_ocr, match_drinks_in_text, extract_volume_from_text
from config import OCR_SPACE_API_KEY

async def test(image_path):
    print(f"Попытка прочитать изображение: {image_path}")
    if not os.path.exists(image_path):
        print(f"❌ Файл не найден: {image_path}")
        return
        
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            
        print("⏳ Запрос к API OCR.space...")
        text = await perform_ocr(image_bytes, api_key=OCR_SPACE_API_KEY)
        
        print("\n=== РАСПОЗНАННЫЙ ТЕКСТ ===")
        print(text if text else "(текст не найден или ошибка API)")
        print("==========================\n")
        
        if text:
            # Тест извлечения объема
            volume = extract_volume_from_text(text)
            print(f"📊 Извлеченный объем: {volume} мл" if volume else "📊 Объём не найден в тексте")
            
            # Тест нечеткого сопоставления напитков
            # Создаем тестовый каталог напитков
            test_drinks = [
                {"id": 1, "name": "Любимая COLA", "calories_per_100ml": 18},
                {"id": 2, "name": "Pepsi Original", "calories_per_100ml": 41},
                {"id": 3, "name": "Добрый Апельсин", "calories_per_100ml": 43},
            ]
            matches = match_drinks_in_text(text, test_drinks)
            print(f"🥤 Найденные напитки ({len(matches)} шт):")
            for m in matches:
                print(f"  - {m['name']} (ID: {m['id']})")
                
    except Exception as e:
        print(f"❌ Произошла ошибка во время теста: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python scratch/test_ocr_space.py <путь_к_изображению>")
        print("Пример: python scratch/test_ocr_space.py C:\\Users\\topor\\Pictures\\cola.jpg")
    else:
        asyncio.run(test(sys.argv[1]))
