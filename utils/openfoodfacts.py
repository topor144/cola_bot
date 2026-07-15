import aiohttp
import logging

logger = logging.getLogger(__name__)

async def get_product_by_barcode(barcode: str) -> dict | None:
    """
    Ищет продукт в базе Open Food Facts по штрихкоду.
    Возвращает словарь с нужными данными или None.
    """
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                if data.get("status") != 1:
                    return None
                    
                product = data.get("product", {})
                nutriments = product.get("nutriments", {})
                
                # Извлекаем данные (на 100г/мл)
                name = product.get("product_name", product.get("product_name_ru", "Неизвестный напиток"))
                calories = nutriments.get("energy-kcal_100g", 0.0)
                sugar = nutriments.get("sugars_100g", 0.0)
                sodium_g = nutriments.get("sodium_100g", 0.0)
                sodium_mg = sodium_g * 1000 if sodium_g else 0.0
                
                # Кофеин редко бывает точным в OFF, обычно это 0 если не указано
                caffeine = nutriments.get("caffeine_100g", 0.0)
                if caffeine > 0:
                    caffeine *= 1000 # перевод в мг
                else:
                    caffeine = 0.0
                
                return {
                    "name": name,
                    "calories": float(calories) if calories else 0.0,
                    "sugar": float(sugar) if sugar else 0.0,
                    "caffeine": float(caffeine) if caffeine else 0.0,
                    "sodium": float(sodium_mg) if sodium_mg else 0.0,
                }
    except Exception as e:
        logger.error(f"❌ Ошибка обращения к Open Food Facts: {e}")
        return None
