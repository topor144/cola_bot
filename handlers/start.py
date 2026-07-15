"""Обработчик команды /start и основного меню"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import OWNER_USER_ID
from database.supabase_client import db
from utils.formatters import format_drink_list
import logging

router = Router()
logger = logging.getLogger(__name__)


class DummyState(StatesGroup):
    """Пустой state для очистки"""
    dummy = State()


def get_main_keyboard():
    """Основная клавиатура (Inline)"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Новая покупка", callback_data="main_buy")],
            [InlineKeyboardButton(text="📋 История", callback_data="main_history"), 
             InlineKeyboardButton(text="📊 Статистика", callback_data="main_stats")],
            [InlineKeyboardButton(text="⚙️ Администратор", callback_data="main_admin")]
        ]
    )
    return kb


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    """Обработка /start"""
    user_id = message.from_user.id
    
    # Очистить state
    await state.clear()
    
    welcome_text = (
        "👋 Добро пожаловать в трекер покупок напитков!\n\n"
        "Я помогу тебе:\n"
        "🥤 Фиксировать все покупки\n"
        "📊 Вести статистику потребления\n"
        "💰 Отслеживать расходы\n\n"
        "Используй кнопки ниже для управления!"
    )
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())


@router.message(Command("help"))
async def help_handler(message: Message):
    """Обработка /help"""
    help_text = (
        "📚 Справка по командам:\n\n"
        "🛒 /buy — Записать новую покупку\n"
        "📋 /history — История покупок\n"
        "📊 /stats — Статистика\n"
        "⚙️ /admin — Панель администратора\n"
        "❓ /help — Эта справка\n\n"
        "Или используй кнопки основного меню!"
    )
    await message.answer(help_text)


@router.message(Command("admin"))
async def admin_command(message: Message, state: FSMContext):
    """Команда /admin"""
    user_id = message.from_user.id
    
    # Проверка прав
    if user_id != OWNER_USER_ID:
        await message.answer("❌ У тебя нет прав на эту команду")
        return
    
    await admin_menu(message, state)


async def admin_menu(source, state: FSMContext):
    """Меню администратора"""
    await state.clear()
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить напиток", callback_data="admin_add_drink")],
            [InlineKeyboardButton(text="📋 Просмотр напитков", callback_data="admin_view_drinks")],
            [InlineKeyboardButton(text="🔄 Бэкап в Excel", callback_data="admin_sync")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")]
        ]
    )
    
    if hasattr(source, 'message'):
        await source.message.edit_text("⚙️ Панель администратора", reply_markup=kb)
    else:
        await source.answer("⚙️ Панель администратора", reply_markup=kb)


@router.callback_query(F.data == "main_admin")
async def admin_button(callback: CallbackQuery, state: FSMContext):
    """Кнопка администратора"""
    user_id = callback.from_user.id
    if user_id != OWNER_USER_ID:
        await callback.answer("❌ У тебя нет прав", show_alert=True)
        return
    await admin_menu(callback, state)


@router.callback_query(F.data == "main_buy")
async def buy_button(callback: CallbackQuery, state: FSMContext):
    """Кнопка новая покупка"""
    from handlers.buy import start_buy
    await start_buy(callback, state)


@router.callback_query(F.data == "main_history")
async def history_button(callback: CallbackQuery, state: FSMContext):
    """Кнопка история"""
    from handlers.history import show_history
    await show_history(callback, state)


@router.callback_query(F.data == "main_stats")
async def stats_button(callback: CallbackQuery, state: FSMContext):
    """Кнопка статистика"""
    from handlers.stats import show_stats
    await show_stats(callback, state)


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    """Возврат из админ меню"""
    await state.clear()
    welcome_text = "👋 Главное меню"
    await callback.message.edit_text(welcome_text, reply_markup=get_main_keyboard())
