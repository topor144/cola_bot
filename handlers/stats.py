"""Обработчик команды /stats"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.supabase_client import db
from utils.formatters import format_stats
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("stats"))
async def stats_command(message: Message, state: FSMContext):
    """Команда /stats"""
    await show_stats(message, state)


async def show_stats(source, state: FSMContext):
    """Показать статистику"""
    user_id = source.from_user.id if hasattr(source, 'from_user') else source.from_user.id
    
    # Получить статистику за последний месяц
    stats = await db.get_stats(user_id, days=30)
    
    stats_text = format_stats(stats)
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 За 7 дней", callback_data="stats_week")],
            [InlineKeyboardButton(text="📊 За месяц", callback_data="stats_month")],
            [InlineKeyboardButton(text="📈 За квартал", callback_data="stats_quarter")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="stats_back")]
        ]
    )
    
    if hasattr(source, 'message'):
        await source.message.edit_text(stats_text, reply_markup=kb)
    else:
        await source.answer(stats_text, reply_markup=kb)


@router.callback_query(F.data == "stats_week")
async def stats_week(callback: CallbackQuery):
    """Статистика за неделю"""
    user_id = callback.from_user.id
    
    stats = await db.get_stats(user_id, days=7)
    text = "📊 Статистика за последние 7 дней\n\n"
    
    if stats.get('total_purchases', 0) == 0:
        text += "❌ Нет данных"
    else:
        avg_price = stats['total_spent'] / stats['total_purchases'] if stats['total_purchases'] > 0 else 0
        total_liters = stats['total_volume'] / 1000
        
        text += (
            f"📈 Всего покупок: {stats['total_purchases']}\n"
            f"💰 Потрачено: {stats['total_spent']:.0f} ₽\n"
            f"💵 Средняя цена: {avg_price:.0f} ₽\n\n"
            f"📦 Всего выпито: {total_liters:.1f} л\n"
            f"🔥 Всего калорий: {stats['total_calories']:.0f} ккал\n"
            f"🍬 Всего сахара: {stats['total_sugar']:.0f} г\n"
            f"☕ Всего кофеина: {stats['total_caffeine']:.0f} мг"
        )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад", callback_data="stats_back")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "stats_month")
async def stats_month(callback: CallbackQuery):
    """Статистика за месяц"""
    user_id = callback.from_user.id
    
    stats = await db.get_stats(user_id, days=30)
    text = "📊 Статистика за последний месяц\n\n"
    
    if stats.get('total_purchases', 0) == 0:
        text += "❌ Нет данных"
    else:
        avg_price = stats['total_spent'] / stats['total_purchases'] if stats['total_purchases'] > 0 else 0
        total_liters = stats['total_volume'] / 1000
        
        text += (
            f"📈 Всего покупок: {stats['total_purchases']}\n"
            f"💰 Потрачено: {stats['total_spent']:.0f} ₽\n"
            f"💵 Средняя цена: {avg_price:.0f} ₽\n\n"
            f"📦 Всего выпито: {total_liters:.1f} л\n"
            f"🔥 Всего калорий: {stats['total_calories']:.0f} ккал\n"
            f"🍬 Всего сахара: {stats['total_sugar']:.0f} г\n"
            f"☕ Всего кофеина: {stats['total_caffeine']:.0f} мг"
        )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад", callback_data="stats_back")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "stats_quarter")
async def stats_quarter(callback: CallbackQuery):
    """Статистика за квартал"""
    user_id = callback.from_user.id
    
    stats = await db.get_stats(user_id, days=90)
    text = "📊 Статистика за последний квартал (90 дней)\n\n"
    
    if stats.get('total_purchases', 0) == 0:
        text += "❌ Нет данных"
    else:
        avg_price = stats['total_spent'] / stats['total_purchases'] if stats['total_purchases'] > 0 else 0
        total_liters = stats['total_volume'] / 1000
        
        text += (
            f"📈 Всего покупок: {stats['total_purchases']}\n"
            f"💰 Потрачено: {stats['total_spent']:.0f} ₽\n"
            f"💵 Средняя цена: {avg_price:.0f} ₽\n\n"
            f"📦 Всего выпито: {total_liters:.1f} л\n"
            f"🔥 Всего калорий: {stats['total_calories']:.0f} ккал\n"
            f"🍬 Всего сахара: {stats['total_sugar']:.0f} г\n"
            f"☕ Всего кофеина: {stats['total_caffeine']:.0f} мг"
        )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад", callback_data="stats_back")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "stats_back")
async def stats_back(callback: CallbackQuery, state: FSMContext):
    """Назад из статистики"""
    await state.clear()
    
    from handlers.start import get_main_keyboard
    await callback.message.delete()
    await callback.message.answer("↩️ Вернулись в основное меню", reply_markup=get_main_keyboard())
