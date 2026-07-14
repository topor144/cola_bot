"""Обработчик администратора - управление напитками"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import OWNER_USER_ID
from database.supabase_client import db
from utils.validators import validate_drink_name, validate_nutrition_value
from utils.formatters import format_drink_list
import logging

router = Router()
logger = logging.getLogger(__name__)


class AddDrinkState(StatesGroup):
    name = State()
    calories = State()
    sugar = State()
    caffeine = State()
    sodium = State()
    volume_default = State()


class EditDrinkState(StatesGroup):
    choosing = State()
    name = State()
    calories = State()
    sugar = State()
    caffeine = State()
    sodium = State()


@router.callback_query(F.data == "admin_add_drink")
async def add_drink_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление напитка"""
    user_id = callback.from_user.id
    
    if user_id != OWNER_USER_ID:
        await callback.answer("❌ Только владелец может добавлять напитки", show_alert=True)
        return
    
    await callback.message.edit_text("🥤 Введи название напитка:")
    await state.set_state(AddDrinkState.name)


@router.message(AddDrinkState.name)
async def add_drink_name(message: Message, state: FSMContext):
    """Ввод названия напитка"""
    name = validate_drink_name(message.text)
    
    if name is None:
        await message.answer("❌ Название должно быть от 2 до 100 символов")
        return
    
    await state.update_data(name=name)
    await message.answer("🔥 Сколько калорий на 100мл? (например: 18)")
    await state.set_state(AddDrinkState.calories)


@router.message(AddDrinkState.calories)
async def add_drink_calories(message: Message, state: FSMContext):
    """Ввод калорий на 100мл"""
    calories = validate_nutrition_value(message.text)
    
    if calories is None:
        await message.answer("❌ Введи корректное значение (0-1000)")
        return
    
    await state.update_data(calories=calories)
    await message.answer("🍬 Сколько сахара на 100мл в граммах? (например: 4.6)")
    await state.set_state(AddDrinkState.sugar)


@router.message(AddDrinkState.sugar)
async def add_drink_sugar(message: Message, state: FSMContext):
    """Ввод сахара на 100мл"""
    sugar = validate_nutrition_value(message.text)
    
    if sugar is None:
        await message.answer("❌ Введи корректное значение (0-1000)")
        return
    
    await state.update_data(sugar=sugar)
    await message.answer("☕ Сколько кофеина на 100мл в мг? (например: 34)")
    await state.set_state(AddDrinkState.caffeine)


@router.message(AddDrinkState.caffeine)
async def add_drink_caffeine(message: Message, state: FSMContext):
    """Ввод кофеина на 100мл"""
    caffeine = validate_nutrition_value(message.text)
    
    if caffeine is None:
        await message.answer("❌ Введи корректное значение (0-1000)")
        return
    
    await state.update_data(caffeine=caffeine)
    await message.answer("🧂 Сколько натрия на 100мл в мг? (например: 30)")
    await state.set_state(AddDrinkState.sodium)


@router.message(AddDrinkState.sodium)
async def add_drink_sodium(message: Message, state: FSMContext):
    """Ввод натрия на 100мл"""
    sodium = validate_nutrition_value(message.text)
    
    if sodium is None:
        await message.answer("❌ Введи корректное значение (0-1000)")
        return
    
    await state.update_data(sodium=sodium)
    await message.answer("📦 Введи объём по умолчанию в мл (обычно 2000):")
    await state.set_state(AddDrinkState.volume_default)


@router.message(AddDrinkState.volume_default)
async def add_drink_volume(message: Message, state: FSMContext):
    """Ввод объёма по умолчанию"""
    from utils.validators import validate_int
    volume = validate_int(message.text, min_val=100, max_val=10000)
    
    if volume is None:
        await message.answer("❌ Введи корректный объём (100-10000 мл)")
        return
    
    # Получить все данные
    data = await state.get_data()
    user_id = message.from_user.id
    
    try:
        # Сохранить напиток в БД
        await db.add_drink(
            name=data['name'],
            user_id=user_id,
            calories=data['calories'],
            sugar=data['sugar'],
            caffeine=data['caffeine'],
            sodium=data['sodium'],
            volume_default=volume
        )
        
        confirmation = (
            f"✅ Напиток добавлен!\n\n"
            f"🥤 {data['name']}\n"
            f"📦 Объём: {volume} мл\n"
            f"🔥 Калории: {data['calories']} ккал/100мл\n"
            f"🍬 Сахар: {data['sugar']} г/100мл\n"
            f"☕ Кофеин: {data['caffeine']} мг/100мл\n"
            f"🧂 Натрий: {data['sodium']} мг/100мл"
        )
        
        await message.answer(confirmation)
        
        # Вернуться в админ меню
        from handlers.start import admin_menu
        await admin_menu(message, state)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении напитка: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()


@router.callback_query(F.data == "admin_view_drinks")
async def view_drinks(callback: CallbackQuery, state: FSMContext):
    """Просмотр напитков"""
    user_id = callback.from_user.id
    
    if user_id != OWNER_USER_ID:
        await callback.answer("❌ Только владелец может просматривать напитки", show_alert=True)
        return
    
    drinks = await db.get_all_drinks(user_id)
    
    if not drinks:
        await callback.message.edit_text("❌ Напитки не добавлены")
        return
    
    # Создать клавиатуру
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"✏️ {drink['name']}", callback_data=f"admin_edit_{drink['id']}"),
             InlineKeyboardButton(text="🗑️", callback_data=f"admin_del_{drink['id']}")]
            for drink in drinks
        ] + [
            [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")]
        ]
    )
    
    text = format_drink_list(drinks)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("admin_del_"))
async def delete_drink(callback: CallbackQuery, state: FSMContext):
    """Удалить напиток"""
    user_id = callback.from_user.id
    drink_id = int(callback.data.split("_")[-1])
    
    if user_id != OWNER_USER_ID:
        await callback.answer("❌ Только владелец может удалять", show_alert=True)
        return
    
    try:
        await db.delete_drink(drink_id, user_id)
        await callback.answer("✅ Напиток удалён", show_alert=True)
        
        # Обновить список
        await view_drinks(callback, state)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении напитка: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data == "admin_sync")
async def sync_handler(callback: CallbackQuery, state: FSMContext):
    """Экспорт в локальный Excel файл (Резервная копия)"""
    user_id = callback.from_user.id
    
    if user_id != OWNER_USER_ID:
        await callback.answer("❌ Только владелец имеет доступ", show_alert=True)
        return
    
    await callback.message.edit_text(
        "⏳ Создание резервной копии Excel...\n\n"
        "Пожалуйста, подожди..."
    )
    
    try:
        from sheets.sync import export_to_excel
        # Экспорт в локальный Excel
        excel_path = r"C:\Users\topor\Downloads\Cola_Tracker.xlsx"
        await export_to_excel(user_id, excel_path)
        
        await callback.message.edit_text(
            "✅ Резервная копия успешно создана!\n\n"
            "Файл Cola_Tracker.xlsx обновлен на вашем ПК."
        )
        
        # Вернуться в админ меню
        from handlers.start import admin_menu
        await admin_menu(callback.message, state)
        
    except Exception as e:
        logger.error(f"❌ Ошибка бэкапа Excel: {e}")
        await callback.message.edit_text(
            f"⚠️ Ошибка бэкапа Excel:\n{str(e)}"
        )
        
        await state.update_data(sync_error=True)
