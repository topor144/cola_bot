"""Обработчик команды /buy и записи покупок"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.supabase_client import db
from utils.calculations import calculate_nutrition, format_nutrition
from utils.validators import validate_price, validate_volume
from utils.formatters import format_purchase_confirmation
import logging

router = Router()
logger = logging.getLogger(__name__)


class BuyState(StatesGroup):
    choosing_drink = State()
    choosing_volume = State()
    custom_volume = State()
    entering_price = State()


@router.message(Command("buy"))
async def buy_command(message: Message, state: FSMContext):
    """Команда /buy"""
    await start_buy(message, state)


async def start_buy(message: Message, state: FSMContext):
    """Начать процесс покупки"""
    user_id = message.from_user.id
    
    # Получить напитки пользователя
    drinks = await db.get_all_drinks(user_id)
    
    if not drinks:
        await message.answer("❌ Добавь напитки сначала через /admin")
        return
    
    # Создать inline клавиатуру с напитками
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🥤 {drink['name']}", callback_data=f"buy_drink_{drink['id']}")]
            for drink in drinks
        ]
    )
    
    await message.answer("🛒 Какой напиток ты купил?", reply_markup=kb)
    await state.set_state(BuyState.choosing_drink)


@router.callback_query(BuyState.choosing_drink, F.data.startswith("buy_drink_"))
async def choose_drink(callback: CallbackQuery, state: FSMContext):
    """Выбор напитка"""
    user_id = callback.from_user.id
    drink_id = int(callback.data.split("_")[-1])
    
    # Получить информацию о напитке
    drink = await db.get_drink_by_id(drink_id, user_id)
    if not drink:
        await callback.answer("❌ Напиток не найден")
        return
    
    # Сохранить в state
    await state.update_data(drink_id=drink_id, drink=drink)
    
    # Показать выбор объёма
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="0.5л (500мл)", callback_data="buy_vol_500")],
            [InlineKeyboardButton(text="1л (1000мл)", callback_data="buy_vol_1000")],
            [InlineKeyboardButton(text="1.5л (1500мл)", callback_data="buy_vol_1500")],
            [InlineKeyboardButton(text="2л (2000мл)", callback_data="buy_vol_2000")],
            [InlineKeyboardButton(text="2.5л (2500мл)", callback_data="buy_vol_2500")],
            [InlineKeyboardButton(text="🔢 Другой объём", callback_data="buy_vol_custom")]
        ]
    )
    
    await callback.message.edit_text(
        f"📦 Выбери объём для {drink['name']}:",
        reply_markup=kb
    )
    await state.set_state(BuyState.choosing_volume)


@router.callback_query(BuyState.choosing_volume, F.data.startswith("buy_vol_"))
async def choose_volume(callback: CallbackQuery, state: FSMContext):
    """Выбор объёма"""
    volume_str = callback.data.split("_")[-1]
    
    if volume_str == "custom":
        await callback.message.edit_text("🔢 Введи объём в миллилитрах (например: 330):")
        await state.set_state(BuyState.custom_volume)
        return
    
    # Получить объём
    volume_ml = int(volume_str)
    await state.update_data(volume_ml=volume_ml)
    
    # Показать расчёты и попросить цену
    await show_nutrition_and_ask_price(callback, state)


@router.message(BuyState.custom_volume)
async def custom_volume_input(message: Message, state: FSMContext):
    """Ввод пользовательского объёма"""
    volume = validate_volume(message.text)
    
    if volume is None:
        await message.answer("❌ Введи корректный объём (100-10000 мл)")
        return
    
    await state.update_data(volume_ml=volume)
    await show_nutrition_and_ask_price(message, state)


async def show_nutrition_and_ask_price(source, state: FSMContext):
    """Показать пищевую ценность и попросить цену"""
    data = await state.get_data()
    drink = data['drink']
    volume_ml = data['volume_ml']
    
    # Рассчитать пищевую ценность
    nutrition = calculate_nutrition(
        drink['calories_per_100ml'],
        drink['sugar_per_100ml'],
        drink['caffeine_per_100ml'],
        drink['sodium_per_100ml'],
        volume_ml
    )
    
    # Сохранить в state
    await state.update_data(nutrition=nutrition)
    
    # Показать информацию
    message_text = (
        f"🥤 {drink['name']}\n"
        f"📦 {volume_ml} мл\n\n"
        f"Пищевая ценность на этот объём:\n"
        f"{format_nutrition(nutrition)}\n\n"
        f"💰 Введи цену в рублях:"
    )
    
    if hasattr(source, 'message'):
        await source.message.edit_text(message_text)
    else:
        await source.answer(message_text)
    
    await state.set_state(BuyState.entering_price)


@router.message(BuyState.entering_price)
async def enter_price(message: Message, state: FSMContext):
    """Ввод цены и финализация покупки"""
    user_id = message.from_user.id
    price = validate_price(message.text)
    
    if price is None:
        await message.answer("❌ Введи корректную цену (0-10000 ₽)")
        return
    
    # Получить данные
    data = await state.get_data()
    drink_id = data['drink_id']
    drink = data['drink']
    volume_ml = data['volume_ml']
    nutrition = data['nutrition']
    
    try:
        # Сохранить покупку в БД
        await db.add_purchase(
            drink_id=drink_id,
            user_id=user_id,
            volume_ml=volume_ml,
            price_rub=price,
            calories=nutrition['calories'],
            sugar=nutrition['sugar'],
            caffeine=nutrition['caffeine'],
            sodium=nutrition['sodium']
        )
        
        # Показать подтверждение
        confirmation = format_purchase_confirmation(
            drink['name'],
            volume_ml,
            price,
            nutrition
        )
        
        await message.answer(confirmation)
        
        # Вернуться в основное меню
        await state.clear()
        from handlers.start import get_main_keyboard
        await message.answer("Что дальше?", reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении покупки: {e}")
        await message.answer(f"❌ Ошибка при сохранении: {str(e)}")
        await state.clear()
