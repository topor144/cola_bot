"""Обработчик команды /history"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.supabase_client import db
from utils.formatters import format_history
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("history"))
async def history_command(message: Message, state: FSMContext):
    """Команда /history"""
    await show_history(message, state)


async def show_history(source, state: FSMContext):
    """Показать историю покупок"""
    user_id = source.from_user.id if hasattr(source, 'from_user') else source.from_user.id
    
    # Получить покупки
    purchases = await db.get_purchases(user_id, limit=10, offset=0)
    
    # Форматировать
    history_text = format_history(purchases)
    
    # Создать клавиатуру
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Сегодня", callback_data="hist_today")],
            [InlineKeyboardButton(text="📆 Неделя", callback_data="hist_week")],
            [InlineKeyboardButton(text="📊 Месяц", callback_data="hist_month")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="hist_back")]
        ]
    )
    
    if hasattr(source, 'message'):
        await source.message.edit_text(history_text, reply_markup=kb)
    else:
        await source.answer(history_text, reply_markup=kb)


@router.callback_query(F.data == "hist_today")
async def history_today(callback: CallbackQuery, state: FSMContext):
    """История за сегодня"""
    from datetime import datetime
    user_id = callback.from_user.id
    
    today = datetime.now().date().isoformat()
    purchases = await db.get_purchases_by_date(user_id, today)
    
    if not purchases:
        text = "❌ Сегодня покупок нет"
    else:
        text = "📋 История за сегодня:\n\n"
        for idx, p in enumerate(purchases, 1):
            drink_name = p['drinks']['name'] if isinstance(p.get('drinks'), dict) else 'Неизвестно'
            text += (
                f"{idx}. 🥤 {drink_name}\n"
                f"   📦 {p['volume_ml']} мл\n"
                f"   💰 {p.get('price_rub', 0)} ₽\n\n"
            )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад", callback_data="hist_back")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "hist_week")
async def history_week(callback: CallbackQuery, state: FSMContext):
    """История за неделю"""
    from datetime import datetime, timedelta
    user_id = callback.from_user.id
    
    week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
    purchases = await db.get_purchases(user_id, limit=50, offset=0)
    
    # Отфильтровать за неделю
    week_purchases = [p for p in purchases if p['purchase_date'] >= week_ago]
    
    if not week_purchases:
        text = "❌ На этой неделе покупок нет"
    else:
        text = f"📋 История за последние 7 дней ({len(week_purchases)} покупок):\n\n"
        for idx, p in enumerate(week_purchases, 1):
            drink_name = p['drinks']['name'] if isinstance(p.get('drinks'), dict) else 'Неизвестно'
            text += (
                f"{idx}. 🥤 {drink_name}\n"
                f"   📦 {p['volume_ml']} мл | 💰 {p.get('price_rub', 0)} ₽\n"
                f"   📅 {p['purchase_date']}\n\n"
            )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад", callback_data="hist_back")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "hist_month")
async def history_month(callback: CallbackQuery, state: FSMContext):
    """История за месяц"""
    from datetime import datetime, timedelta
    user_id = callback.from_user.id
    
    month_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
    purchases = await db.get_purchases(user_id, limit=100, offset=0)
    
    # Отфильтровать за месяц
    month_purchases = [p for p in purchases if p['purchase_date'] >= month_ago]
    
    if not month_purchases:
        text = "❌ За этот месяц покупок нет"
    else:
        text = f"📋 История за последние 30 дней ({len(month_purchases)} покупок):\n\n"
        for idx, p in enumerate(month_purchases, 1):
            drink_name = p['drinks']['name'] if isinstance(p.get('drinks'), dict) else 'Неизвестно'
            text += (
                f"{idx}. 🥤 {drink_name}\n"
                f"   📦 {p['volume_ml']} мл | 💰 {p.get('price_rub', 0)} ₽\n"
                f"   📅 {p['purchase_date']}\n\n"
            )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад", callback_data="hist_back")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "hist_back")
async def history_back(callback: CallbackQuery, state: FSMContext):
    """Назад из истории"""
    await state.clear()
    
    from handlers.start import get_main_keyboard
    await callback.message.delete()
    await callback.message.answer("↩️ Вернулись в основное меню", reply_markup=get_main_keyboard())
