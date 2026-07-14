import re
import logging
import requests
import asyncio

logger = logging.getLogger(__name__)


async def perform_ocr(image_bytes: bytes, api_key: str = "helloworld", language: str = "rus") -> str:
    """
    Отправляет изображение в бесплатное API OCR.space для распознавания текста.
    Запускается асинхронно с использованием библиотеки requests.
    """
    try:
        payload = {
            'apikey': api_key,
            'language': language,
            'isOverlayRequired': False,
            'scale': True,        # Улучшает распознавание на маленьких шрифтах
            'OCREngine': 2        # Engine 2 лучше распознает чеки и таблицы
        }
        files = {
            'image.png': image_bytes
        }
        
        # Выполняем POST запрос
        response = await asyncio.to_thread(
            lambda: requests.post(
                'https://api.ocr.space/parse/image',
                files=files,
                data=payload,
                timeout=20
            )
        )
        
        if response.status_code != 200:
            logger.error(f"OCR.space API вернул HTTP {response.status_code}")
            return ""
            
        result = response.json()
        
        if result.get('OCRExitCode') == 1:
            parsed_text = ""
            for res in result.get('ParsedResults', []):
                text = res.get('ParsedText', "")
                if text:
                    parsed_text += text + "\n"
            return parsed_text
        else:
            error_msg = result.get('ErrorMessage', 'Неизвестная ошибка API')
            logger.error(f"OCR.space ошибка: {error_msg}")
            return ""
            
    except Exception as e:
        logger.error(f"Ошибка при вызове OCR.space API: {e}")
        return ""


def match_drinks_in_text(text: str, drinks: list) -> list:
    """
    Ищет соответствие текста с каталогом напитков.
    Возвращает список совпавших напитков.
    """
    if not text or not drinks:
        return []
        
    text_lower = text.lower()
    matched = []
    
    for drink in drinks:
        name = drink['name'].lower()
        
        # 1. Прямое совпадение полного имени
        if name in text_lower:
            matched.append(drink)
            continue
            
        # 2. Совпадение по словам (если напиток состоит из нескольких слов, например "Любимая Cola")
        words = name.split()
        if len(words) > 1:
            # Исключаем слишком короткие слова типа предлогов
            significant_words = [w for w in words if len(w) > 2]
            if significant_words and all(w in text_lower for w in significant_words):
                matched.append(drink)
                continue
                
        # 3. Дополнительно проверяем перестановку символов английской/русской раскладки для популярных слов (C/С, O/О)
        # На случай, если OCR перепутал русское 'С' и английское 'C'
        normalized_name = name.replace('c', 'с').replace('o', 'о').replace('a', 'а').replace('p', 'р')
        normalized_text = text_lower.replace('c', 'с').replace('o', 'о').replace('a', 'а').replace('p', 'р')
        if normalized_name in normalized_text:
            matched.append(drink)
            
    # Удаляем дубликаты по ID напитка
    unique_matches = []
    seen_ids = set()
    for d in matched:
        if d['id'] not in seen_ids:
            unique_matches.append(d)
            seen_ids.add(d['id'])
            
    return unique_matches


def extract_volume_from_text(text: str) -> int | None:
    """
    Извлекает объем напитка из текста с помощью регулярных выражений.
    Поддерживает форматы: 0.5л, 1.5 л, 2л, 330мл, 1 l, 500 ml и т.д.
    Возвращает объем в миллилитрах.
    """
    if not text:
        return None
        
    text_lower = text.lower()
    
    # 1. Поиск миллилитров (мл, ml)
    ml_matches = re.findall(r"(\d+)\s*(мл|ml)", text_lower)
    if ml_matches:
        try:
            # Возвращаем наибольшее найденное значение, похожее на объем напитка
            volumes = [int(val) for val, _ in ml_matches if 100 <= int(val) <= 10000]
            if volumes:
                return max(volumes)
        except ValueError:
            pass
            
    # 2. Поиск литров (л, l, литр, литра, литров)
    l_matches = re.findall(r"(\d+[\.,]?\d*)\s*(л|l|литр)", text_lower)
    if l_matches:
        for val_str, _ in l_matches:
            val_str = val_str.replace(",", ".")
            try:
                val = float(val_str)
                # Если значение похоже на литры (от 0.1 до 10 литров)
                if 0.1 <= val <= 10.0:
                    return int(val * 1000)
            except ValueError:
                pass
                
    return None
