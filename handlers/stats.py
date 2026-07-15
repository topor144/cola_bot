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


from aiogram.types import BufferedInputFile
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta

def create_stats_chart(purchases, period_name: str) -> BufferedInputFile | None:
    """Генерация круговой диаграммы (топ-5 напитков) и столбчатой диаграммы по дням"""
    if not purchases:
        return None
        
    # Агрегация данных по напиткам
    drink_counts = {}
    for p in purchases:
        name = p['drinks']['name'] if isinstance(p.get('drinks'), dict) else str(p.get('drink_id', 'Неизвестно'))
        drink_counts[name] = drink_counts.get(name, 0) + p.get('volume_ml', 0)
        
    if not drink_counts:
        return None
        
    # Топ-5 напитков
    sorted_drinks = sorted(drink_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    labels = [k for k, v in sorted_drinks]
    sizes = [v for k, v in sorted_drinks]
    
    # Настройка графика
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#1e1e1e')
    
    # Рисуем Pie chart
    colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99', '#c2c2f0']
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, textprops={'color': 'white'})
    ax.axis('equal')
    
    plt.title(f'Топ напитков по объему ({period_name})', color='white', pad=20)
    
    # Сохраняем в память
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    buf.seek(0)
    plt.close()
    
    return BufferedInputFile(buf.getvalue(), filename="stats.png")


async def _send_stats_photo(callback: CallbackQuery, days: int, period_name: str):
    user_id = callback.from_user.id
    
    # Получаем данные
    purchases = await db.get_all_purchases(user_id)
    date_limit = datetime.now() - timedelta(days=days)
    
    filtered_purchases = []
    for p in purchases:
        try:
            p_date = datetime.strptime(p["purchase_date"], "%d.%m.%Y")
            if p_date >= date_limit:
                filtered_purchases.append(p)
        except Exception:
            filtered_purchases.append(p)
            
    stats = await db.get_stats(user_id, days=days)
    
    if stats.get('total_purchases', 0) == 0:
        text = f"❌ Нет данных за {period_name}"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="↩️ Назад", callback_data="stats_back")]])
        await callback.message.edit_text(text, reply_markup=kb)
        return

    avg_price = stats['total_spent'] / stats['total_purchases'] if stats['total_purchases'] > 0 else 0
    total_liters = stats['total_volume'] / 1000
    
    text = (
        f"📊 Статистика ({period_name})\n\n"
        f"📈 Всего покупок: {stats['total_purchases']}\n"
        f"💰 Потрачено: {stats['total_spent']:.0f} ₽\n"
        f"💵 Средняя цена: {avg_price:.0f} ₽\n\n"
        f"📦 Всего выпито: {total_liters:.1f} л\n"
        f"🔥 Всего калорий: {stats['total_calories']:.0f} ккал\n"
        f"🍬 Всего сахара: {stats['total_sugar']:.0f} г\n"
        f"☕ Всего кофеина: {stats['total_caffeine']:.0f} мг"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="↩️ Назад", callback_data="stats_back")]])
    
    # Генерируем график
    photo = create_stats_chart(filtered_purchases, period_name)
    
    if photo:
        await callback.message.delete()
        await callback.message.answer_photo(photo=photo, caption=text, reply_markup=kb)
    else:
        await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "stats_week")
async def stats_week(callback: CallbackQuery):
    await _send_stats_photo(callback, 7, "последние 7 дней")


@router.callback_query(F.data == "stats_month")
async def stats_month(callback: CallbackQuery):
    await _send_stats_photo(callback, 30, "последний месяц")


@router.callback_query(F.data == "stats_quarter")
async def stats_quarter(callback: CallbackQuery):
    await _send_stats_photo(callback, 90, "последний квартал (90 дней)")


@router.callback_query(F.data == "stats_back")
async def stats_back(callback: CallbackQuery, state: FSMContext):
    """Назад из статистики"""
    await state.clear()
    
    from handlers.start import get_main_keyboard
    await callback.message.edit_text("👋 Главное меню", reply_markup=get_main_keyboard())
