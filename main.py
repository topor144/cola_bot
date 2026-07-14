"""Главный файл Telegram бота"""

import os
import asyncio
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.types import BotCommand, TelegramObject
from config import TELEGRAM_BOT_TOKEN, OWNER_USER_ID, LOG_LEVEL
from handlers import start, buy, history, stats, admin, photo

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# --- Обход ограничений Render (Dummy Web Server) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    """Мини-обработчик для ответов на пинги Render"""
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Бот запущен и работает! 🥤".encode("utf-8"))

    def log_message(self, format, *args):
        # Подавляем лишние логи пингов от Render
        pass


def run_dummy_server():
    """Запуск HTTP-сервера для прохождения Health Check на Render"""
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🌐 Запускаю Health Check веб-сервер на порту {port}...")
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Не удалось запустить Health Check сервер: {e}")


# --- Инициализация ключей Google из переменных окружения ---
def setup_credentials():
    """
    Если credentials.json отсутствует (например, на сервере Render),
    создает его из переменной окружения GOOGLE_SHEETS_CREDENTIALS_JSON_CONTENT.
    """
    credentials_path = "./credentials.json"
    if not os.path.exists(credentials_path):
        content = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON_CONTENT")
        if content:
            try:
                with open(credentials_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info("✅ credentials.json успешно воссоздан из переменных окружения!")
            except Exception as e:
                logger.error(f"❌ Не удалось записать credentials.json: {e}")
        else:
            logger.warning("⚠️ Файл credentials.json отсутствует и переменная GOOGLE_SHEETS_CREDENTIALS_JSON_CONTENT не задана.")


class OwnerOnlyMiddleware(BaseMiddleware):
    """Middleware для ограничения доступа к боту только для владельца"""
    def __init__(self, owner_id: int):
        super().__init__()
        self.owner_id = owner_id

    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = getattr(event, "from_user", None)
        if user and user.id == self.owner_id:
            return await handler(event, data)
            
        logger.warning(f"🔒 Несанкционированный доступ от пользователя {user.id if user else 'Unknown'}")
        
        if isinstance(event, types.Message):
            await event.answer("❌ Этот бот является приватным и доступен только его владельцу.")
        elif isinstance(event, types.CallbackQuery):
            await event.answer("❌ Доступ ограничен.", show_alert=True)
        return


async def set_bot_commands(bot: Bot):
    """Установить команды бота"""
    commands = [
        BotCommand(command="start", description="🏠 Основное меню"),
        BotCommand(command="buy", description="🛒 Записать покупку"),
        BotCommand(command="history", description="📋 История покупок"),
        BotCommand(command="stats", description="📊 Статистика"),
        BotCommand(command="admin", description="⚙️ Администратор"),
        BotCommand(command="help", description="❓ Справка"),
    ]
    
    await bot.set_my_commands(commands)
    logger.info("✅ Команды бота установлены")


async def main():
    """Главная функция"""
    
    # 1. Готовим файл credentials.json из переменных окружения при необходимости
    setup_credentials()
    
    # 2. Запускаем заглушку веб-сервера для Render
    if os.getenv("PORT") or os.getenv("RENDER"):
        threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # 3. Инициализация бота и диспетчера
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрация глобального middleware для авторизации владельца
    dp.message.outer_middleware(OwnerOnlyMiddleware(OWNER_USER_ID))
    dp.callback_query.outer_middleware(OwnerOnlyMiddleware(OWNER_USER_ID))
    
    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(buy.router)
    dp.include_router(history.router)
    dp.include_router(stats.router)
    dp.include_router(admin.router)
    dp.include_router(photo.router)
    
    logger.info("🚀 Бот запускается...")
    
    try:
        # Установить команды
        await set_bot_commands(bot)
        
        # Вывести информацию о боте
        me = await bot.get_me()
        logger.info(f"✅ Бот @{me.username} успешно подключен")
        logger.info(f"📱 Имя: {me.first_name}")
        
        # Запустить polling
        logger.info("⏳ Ожидание сообщений...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        raise
    
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
