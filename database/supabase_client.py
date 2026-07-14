import os
import asyncio
import logging
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient import discovery
from config import GOOGLE_SHEETS_CREDENTIALS_JSON, GOOGLE_SHEETS_ID

logger = logging.getLogger(__name__)

def parse_float(val) -> float:
    if not val or val == '-': return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(',', '.').replace(' ', '')
        return float(val)
    except ValueError:
        return 0.0

def parse_int(val) -> int:
    if not val or val == '-': return 0
    try:
        if isinstance(val, str):
            val = val.replace(' ', '')
        return int(float(val))
    except ValueError:
        return 0

# Scopes для Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


async def _trigger_excel_backup(user_id: int):
    """Фоновый экспорт в локальный Excel файл Cola_Tracker.xlsx"""
    try:
        from sheets.sync import export_to_excel
        excel_path = r"C:\Users\topor\Downloads\Cola_Tracker.xlsx"
        await export_to_excel(user_id, excel_path)
    except Exception as e:
        logger.error(f"⚠️ Не удалось создать локальную копию Excel: {e}")


class GoogleSheetsDatabase:
    """
    Класс-адаптер для использования Google Sheets в качестве основной БД.
    Полностью заменяет Supabase Client, сохраняя сигнатуру вызовов для обработчиков бота.
    """
    
    def __init__(self):
        self._service = None
        self.drinks_cache = []
        
        # Быстрая проверка наличия файла авторизации
        if not os.path.exists(GOOGLE_SHEETS_CREDENTIALS_JSON):
            content = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON_CONTENT")
            if content:
                try:
                    with open(GOOGLE_SHEETS_CREDENTIALS_JSON, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.info("✅ credentials.json успешно воссоздан из переменных окружения!")
                except Exception as e:
                    logger.error(f"❌ Не удалось записать credentials.json: {e}")
                    raise
            else:
                logger.error(f"❌ Файл Google Sheets credentials не найден по пути: {GOOGLE_SHEETS_CREDENTIALS_JSON}")
                raise FileNotFoundError(f"Файл {GOOGLE_SHEETS_CREDENTIALS_JSON} обязателен для запуска бота!")

    def _get_service_sync(self):
        """Синхронно инициализирует Google Sheets Service"""
        if self._service is None:
            credentials = Credentials.from_service_account_file(
                GOOGLE_SHEETS_CREDENTIALS_JSON,
                scopes=SCOPES
            )
            self._service = discovery.build('sheets', 'v4', credentials=credentials)
        return self._service

    async def get_service(self):
        """Асинхронно получает Google Sheets Service"""
        return await asyncio.to_thread(self._get_service_sync)

    # ============ DRINKS (Напитки) ============
    
    async def get_all_drinks(self, user_id: int) -> list:
        """Получить все напитки из вкладки 'Состав напитков'"""
        # Если кэш уже прогрет, отдаем его для быстрой работы бота
        if self.drinks_cache:
            return self.drinks_cache

        try:
            service = await self.get_service()
            # Читаем данные каталога напитков
            result = await asyncio.to_thread(
                service.spreadsheets().values().get(
                    spreadsheetId=GOOGLE_SHEETS_ID,
                    range="Состав напитков!A2:E"
                ).execute
            )
            rows = result.get('values', [])
            
            drinks = []
            for idx, row in enumerate(rows):
                if not row or not row[0]:
                    continue
                # Сопоставляем с моделью БД
                drinks.append({
                    "id": idx + 1,  # В качестве ID используем порядковый номер
                    "name": row[0],
                    "calories_per_100ml": parse_float(row[1]) if len(row) > 1 else 0.0,
                    "sugar_per_100ml": parse_float(row[2]) if len(row) > 2 else 0.0,
                    "caffeine_per_100ml": parse_float(row[3]) if len(row) > 3 else 0.0,
                    "sodium_per_100ml": parse_float(row[4]) if len(row) > 4 else 0.0,
                    "volume_default": 2000  # Значение по умолчанию
                })
            
            self.drinks_cache = drinks
            return drinks
        except Exception as e:
            logger.error(f"❌ Ошибка при получении напитков из Google Sheets: {e}")
            return []

    async def get_drink_by_id(self, drink_id: int, user_id: int) -> dict:
        """Получить напиток по его ID (номеру строки)"""
        drinks = await self.get_all_drinks(user_id)
        for drink in drinks:
            if drink["id"] == drink_id:
                return drink
        return None

    async def add_drink(self, name: str, user_id: int, calories: float, sugar: float, 
                        caffeine: float, sodium: float, volume_default: int = 2000) -> dict:
        """Добавить новый напиток во вкладку 'Состав напитков'"""
        try:
            service = await self.get_service()
            
            # Сначала получим все существующие строки, чтобы найти первую свободную
            result = await asyncio.to_thread(
                service.spreadsheets().values().get(
                    spreadsheetId=GOOGLE_SHEETS_ID,
                    range="Состав напитков!A2:E500"
                ).execute
            )
            rows = result.get('values', [])
            
            # Ищем первую пустую строку
            first_empty_row = 2
            for i, row in enumerate(rows):
                if not row or not row[0]:
                    first_empty_row = i + 2
                    break
            else:
                first_empty_row = len(rows) + 2
                
            row_range = f"Состав напитков!A{first_empty_row}:E{first_empty_row}"
            
            body = {
                "values": [[
                    name,
                    calories,
                    sugar,
                    caffeine,
                    sodium
                ]]
            }
            
            # Записываем
            await asyncio.to_thread(
                service.spreadsheets().values().update(
                    spreadsheetId=GOOGLE_SHEETS_ID,
                    range=row_range,
                    valueInputOption="USER_ENTERED",
                    body=body
                ).execute
            )
            
            # Инвалидируем кэш
            self.drinks_cache = []
            
            new_drink = {
                "id": first_empty_row - 1,
                "name": name,
                "calories_per_100ml": calories,
                "sugar_per_100ml": sugar,
                "caffeine_per_100ml": caffeine,
                "sodium_per_100ml": sodium,
                "volume_default": volume_default
            }
            
            # Сохраняем в резервную локальную копию Excel
            asyncio.create_task(_trigger_excel_backup(user_id))
            
            return new_drink
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении напитка в Google Sheets: {e}")
            raise

    async def delete_drink(self, drink_id: int, user_id: int) -> bool:
        """Удалить напиток (очистить ячейки его строки)"""
        try:
            service = await self.get_service()
            row_idx = drink_id + 1  # Индекс строки в таблице
            
            # Очищаем ячейки в этой строке
            row_range = f"Состав напитков!A{row_idx}:E{row_idx}"
            await asyncio.to_thread(
                service.spreadsheets().values().clear(
                    spreadsheetId=GOOGLE_SHEETS_ID,
                    range=row_range
                ).execute
            )
            
            self.drinks_cache = []
            asyncio.create_task(_trigger_excel_backup(user_id))
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении напитка из Google Sheets: {e}")
            raise

    # ============ PURCHASES (Покупки) ============
    
    async def get_all_purchases(self, user_id: int) -> list:
        """Получить все покупки из вкладки 'Покупки'"""
        try:
            service = await self.get_service()
            result = await asyncio.to_thread(
                service.spreadsheets().values().get(
                    spreadsheetId=GOOGLE_SHEETS_ID,
                    range="Покупки!A2:I2000"
                ).execute
            )
            rows = result.get('values', [])
            
            purchases = []
            for idx, row in enumerate(rows):
                if not row or len(row) < 2 or not row[0]:
                    continue
                
                purchases.append({
                    "id": idx + 1,
                    "purchase_date": row[0],
                    "drinks": {"name": row[1]},
                    "drink_id": row[1],
                    "volume_ml": parse_int(row[2]) if len(row) > 2 else 0,
                    "price_rub": parse_float(row[3]) if len(row) > 3 else 0.0,
                    "calories_total": parse_float(row[4]) if len(row) > 4 else 0.0,
                    "sugar_total": parse_float(row[5]) if len(row) > 5 else 0.0,
                    "caffeine_total": parse_float(row[6]) if len(row) > 6 else 0.0,
                    "sodium_total": parse_float(row[7]) if len(row) > 7 else 0.0,
                    "notes": row[8] if len(row) > 8 else ""
                })
            
            # Показываем самые свежие сверху
            purchases.reverse()
            return purchases
        except Exception as e:
            logger.error(f"❌ Ошибка при получении покупок из Google Sheets: {e}")
            return []

    async def get_purchases(self, user_id: int, limit: int = 10, offset: int = 0) -> list:
        """Получить лимитированный список покупок"""
        purchases = await self.get_all_purchases(user_id)
        return purchases[offset:offset + limit]

    async def get_purchases_by_date(self, user_id: int, date: str) -> list:
        """
        Получить покупки за определенный день.
        Входная дата имеет формат YYYY-MM-DD.
        Конвертируем в DD.MM.YYYY для сопоставления с Google Sheets.
        """
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = dt.strftime("%d.%m.%Y")
        except ValueError:
            formatted_date = date
            
        purchases = await self.get_all_purchases(user_id)
        return [p for p in purchases if p["purchase_date"] == formatted_date]

    async def add_purchase(self, drink_id: int, user_id: int, volume_ml: int, price_rub: float,
                          calories: float, sugar: float, caffeine: float, sodium: float,
                          notes: str = "") -> dict:
        """Записать покупку и пересчитать статистику"""
        try:
            service = await self.get_service()
            
            # Получаем напиток
            drink = await self.get_drink_by_id(drink_id, user_id)
            drink_name = drink["name"] if drink else "Неизвестный напиток"
            
            # Ищем свободную строку в Покупках
            result = await asyncio.to_thread(
                service.spreadsheets().values().get(
                    spreadsheetId=GOOGLE_SHEETS_ID,
                    range="Покупки!A2:I2000"
                ).execute
            )
            rows = result.get('values', [])
            
            first_empty_row = 2
            for i, row in enumerate(rows):
                if not row or not row[0]:
                    first_empty_row = i + 2
                    break
            else:
                first_empty_row = len(rows) + 2
                
            row_range = f"Покупки!A{first_empty_row}:I{first_empty_row}"
            
            today_str = datetime.now().strftime("%d.%m.%Y")
            
            body = {
                "values": [[
                    today_str,
                    drink_name,
                    volume_ml,
                    price_rub,
                    calories,
                    sugar,
                    caffeine,
                    sodium,
                    notes
                ]]
            }
            
            # Записываем покупку
            await asyncio.to_thread(
                service.spreadsheets().values().update(
                    spreadsheetId=GOOGLE_SHEETS_ID,
                    range=row_range,
                    valueInputOption="USER_ENTERED",
                    body=body
                ).execute
            )
            
            # Пересчитываем статистику
            all_purchases = await self.get_all_purchases(user_id)
            # Так как get_all_purchases возвращает отсортированный по убыванию список, добавим новую запись
            new_purchase = {
                "purchase_date": today_str,
                "drinks": {"name": drink_name},
                "volume_ml": volume_ml,
                "price_rub": price_rub,
                "calories_total": calories,
                "sugar_total": sugar,
                "caffeine_total": caffeine,
                "sodium_total": sodium,
                "notes": notes
            }
            all_purchases.append(new_purchase)
            
            # Вычисляем агрегаты
            total_purchases = len(all_purchases)
            total_spent = sum(p.get('price_rub', 0) for p in all_purchases if p.get('price_rub'))
            avg_price = total_spent / total_purchases if total_purchases > 0 else 0
            total_volume_l = sum(p['volume_ml'] for p in all_purchases) / 1000
            avg_volume = sum(p['volume_ml'] for p in all_purchases) / total_purchases if total_purchases > 0 else 0
            total_calories = sum(p.get('calories_total', 0) for p in all_purchases if p.get('calories_total'))
            total_sugar = sum(p.get('sugar_total', 0) for p in all_purchases if p.get('sugar_total'))
            total_caffeine = sum(p.get('caffeine_total', 0) for p in all_purchases if p.get('caffeine_total'))
            total_sodium = sum(p.get('sodium_total', 0) for p in all_purchases if p.get('sodium_total'))
            
            # Формируем тело для записи статистики в Статистика!B2:B10
            stats_body = {
                "values": [
                    [total_purchases],
                    [total_spent],
                    [round(avg_price, 2)],
                    [round(total_volume_l, 2)],
                    [round(avg_volume, 1)],
                    [round(total_calories, 1)],
                    [round(total_sugar, 1)],
                    [round(total_caffeine, 1)],
                    [round(total_sodium, 1)]
                ]
            }
            
            # Записываем статистику
            await asyncio.to_thread(
                service.spreadsheets().values().update(
                    spreadsheetId=GOOGLE_SHEETS_ID,
                    range="Статистика!B2:B10",
                    valueInputOption="USER_ENTERED",
                    body=stats_body
                ).execute
            )
            
            # Запускаем локальный бэкап Excel
            asyncio.create_task(_trigger_excel_backup(user_id))
            
            return new_purchase
        except Exception as e:
            logger.error(f"❌ Ошибка при записи покупки в Google Sheets: {e}")
            raise

    # ============ STATISTICS ============
    
    async def get_stats(self, user_id: int, days: int = 30) -> dict:
        """Рассчитать статистику за определенный период дней"""
        try:
            purchases = await self.get_all_purchases(user_id)
            
            # Фильтруем за указанные дни
            from datetime import timedelta
            date_limit = datetime.now() - timedelta(days=days)
            
            filtered = []
            for p in purchases:
                try:
                    p_date = datetime.strptime(p["purchase_date"], "%d.%m.%Y")
                    if p_date >= date_limit:
                        filtered.append(p)
                except Exception:
                    # На случай неверного формата даты в таблице
                    filtered.append(p)
                    
            if not filtered:
                return {
                    "total_purchases": 0,
                    "total_spent": 0,
                    "total_volume": 0,
                    "total_calories": 0,
                    "total_sugar": 0,
                    "total_caffeine": 0,
                    "total_sodium": 0
                }
            
            return {
                "total_purchases": len(filtered),
                "total_spent": sum(p["price_rub"] for p in filtered if p.get("price_rub")),
                "total_volume": sum(p["volume_ml"] for p in filtered),
                "total_calories": sum(p["calories_total"] for p in filtered if p.get("calories_total")),
                "total_sugar": sum(p["sugar_total"] for p in filtered if p.get("sugar_total")),
                "total_caffeine": sum(p["caffeine_total"] for p in filtered if p.get("caffeine_total")),
                "total_sodium": sum(p["sodium_total"] for p in filtered if p.get("sodium_total")),
            }
        except Exception as e:
            logger.error(f"❌ Ошибка при получении статистики: {e}")
            return {}

    # ============ SYNC LOGS (Для совместимости) ============
    
    async def log_sync(self, user_id: int, status: str, message: str = ""):
        """Совместимость логов синхронизации"""
        logger.info(f"💾 Лог синхронизации: {status} - {message}")


# Экспортируем глобальный экземпляр класса для замены Supabase
db = GoogleSheetsDatabase()
