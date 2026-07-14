"""Главный файл Telegram бота"""

import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.types import BotCommand, TelegramObject
from config import TELEGRAM_BOT_TOKEN, OWNER_USER_ID, LOG_LEVEL
from handlers import start, buy, history, stats, admin

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
        
        # Если событие поддерживает ответ (сообщение или кнопка)
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
    
    # Инициализация бота и диспетчера
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
