import logging
from io import BytesIO
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.supabase_client import db

logger = logging.getLogger(__name__)
router = Router()


class OcrState(StatesGroup):
    confirming_drink = State()
    entering_volume = State()
    entering_price = State()


@router.message(F.photo)
async def photo_handler(message: Message, state: FSMContext):
    """Обработчик отправки фото. Скачивает и распознает его с помощью OCR.space"""
    photo = message.photo[-1]
    bot = message.bot
    
    # 1. Информируем пользователя о начале обработки
    status_msg = await message.answer("⏳ Скачиваю фото и запускаю распознавание через OCR.space...")
    
    try:
        # 2. Скачиваем фото в буфер
        file_info = await bot.get_file(photo.file_id)
        file_data = BytesIO()
        await bot.download_file(file_info.file_path, file_data)
        image_bytes = file_data.getvalue()
        
        # 3. Вызываем API OCR.space
        from utils.ocr_parser import perform_ocr, match_drinks_in_text, extract_volume_from_text
        from config import OCR_SPACE_API_KEY
        
        # Запускаем в фоновом потоке
        ocr_text = await perform_ocr(image_bytes, api_key=OCR_SPACE_API_KEY)
        
        if not ocr_text:
            await status_msg.edit_text("❌ OCR.space не вернул распознанный текст. Убедитесь, что текст на фото четкий и читаемый.")
            return
            
        # 4. Сопоставляем текст с каталогом напитков и ищем объем
        drinks = await db.get_all_drinks(message.from_user.id)
        matched_drinks = match_drinks_in_text(ocr_text, drinks)
        extracted_volume = extract_volume_from_text(ocr_text)
        
        await status_msg.delete()  # Удаляем статус-сообщение
        
        if len(matched_drinks) == 1:
            drink = matched_drinks[0]
            volume = extracted_volume if extracted_volume else drink.get("volume_default", 2000)
            
            await state.update_data(drink=drink, volume_ml=volume)
            
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Подтвердить", callback_data="ocr_confirm_ok")],
                [InlineKeyboardButton(text="✏️ Изменить объем", callback_data="ocr_change_vol")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="ocr_cancel")]
            ])
            
            await message.answer(
                f"🔍 **Распознавание фото**\n\n"
                f"Найдено совпадение с напитком:\n"
                f"🥤 **{drink['name']}**\n"
                f"📦 Распознанный объем: **{volume} мл**\n\n"
                f"Все верно?",
                reply_markup=kb
            )
            await state.set_state(OcrState.confirming_drink)
            
        elif len(matched_drinks) > 1:
            # Найдено несколько совпадений
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"🥤 {d['name']}", callback_data=f"ocr_select_{d['id']}")]
                for d in matched_drinks
            ] + [[InlineKeyboardButton(text="❌ Отмена", callback_data="ocr_cancel")]])
            
            await state.update_data(extracted_volume=extracted_volume)
            
            await message.answer(
                f"🔍 **Распознавание фото**\n\n"
                f"Найдено несколько похожих напитков. Пожалуйста, выберите нужный:",
                reply_markup=kb
            )
            await state.set_state(OcrState.confirming_drink)
            
        else:
            # Ничего не распознано
            text_snippet = ocr_text[:300] + "..." if len(ocr_text) > 300 else ocr_text
            
            # Показываем список первых 5 напитков из базы для ручного выбора
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"🥤 {d['name']}", callback_data=f"ocr_select_{d['id']}")]
                for d in drinks[:5]
            ] + [
                [InlineKeyboardButton(text="🥤 Показать все напитки", callback_data="ocr_list_all")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="ocr_cancel")]
            ])
            
            await state.update_data(extracted_volume=extracted_volume)
            
            await message.answer(
                f"🔍 **Распознавание фото**\n\n"
                f"Не удалось распознать напиток в тексте.\n\n"
                f"Распознанный текст на фото:\n`{text_snippet}`\n\n"
                f"Выберите напиток вручную или нажмите Отмена:",
                reply_markup=kb
            )
            await state.set_state(OcrState.confirming_drink)
            
    except Exception as e:
        logger.error(f"Ошибка в обработчике фото: {e}")
        await message.answer(f"❌ Произошла ошибка при обработке изображения: {e}")
        await state.clear()


@router.callback_query(OcrState.confirming_drink, F.data.startswith("ocr_select_"))
async def select_drink_cb(callback: CallbackQuery, state: FSMContext):
    """Пользователь выбрал напиток из списка"""
    drink_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    drink = await db.get_drink_by_id(drink_id, user_id)
    if not drink:
        await callback.answer("❌ Напиток не найден")
        return
        
    data = await state.get_data()
    extracted_volume = data.get("extracted_volume")
    volume = extracted_volume if extracted_volume else drink.get("volume_default", 2000)
    
    await state.update_data(drink=drink, volume_ml=volume)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="ocr_confirm_ok")],
        [InlineKeyboardButton(text="✏️ Изменить объем", callback_data="ocr_change_vol")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="ocr_cancel")]
    ])
    
    await callback.message.edit_text(
        f"🥤 Выбран напиток: **{drink['name']}**\n"
        f"📦 Объем: **{volume} мл**\n\n"
        f"Все верно?",
        reply_markup=kb
    )


@router.callback_query(OcrState.confirming_drink, F.data == "ocr_list_all")
async def list_all_drinks_cb(callback: CallbackQuery, state: FSMContext):
    """Показать все напитки каталога при ручном поиске"""
    user_id = callback.from_user.id
    drinks = await db.get_all_drinks(user_id)
    
    if not drinks:
        await callback.answer("❌ В базе нет добавленных напитков")
        return
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🥤 {d['name']}", callback_data=f"ocr_select_{d['id']}")]
        for d in drinks
    ] + [[InlineKeyboardButton(text="❌ Отмена", callback_data="ocr_cancel")]])
    
    await callback.message.edit_text(
        "🥤 Выберите напиток из каталога:",
        reply_markup=kb
    )


@router.callback_query(OcrState.confirming_drink, F.data == "ocr_confirm_ok")
async def confirm_ok_cb(callback: CallbackQuery, state: FSMContext):
    """Пользователь подтвердил напиток и объем"""
    await callback.message.edit_text("💰 Введите цену покупки в рублях:")
    await state.set_state(OcrState.entering_price)


@router.callback_query(OcrState.confirming_drink, F.data == "ocr_change_vol")
async def change_vol_cb(callback: CallbackQuery, state: FSMContext):
    """Пользователь хочет изменить объем"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="0.5л (500мл)", callback_data="ocr_vol_500")],
        [InlineKeyboardButton(text="1л (1000мл)", callback_data="ocr_vol_1000")],
        [InlineKeyboardButton(text="1.5л (1500мл)", callback_data="ocr_vol_1500")],
        [InlineKeyboardButton(text="2л (2000мл)", callback_data="ocr_vol_2000")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="ocr_cancel")]
    ])
    await callback.message.edit_text(
        "📦 Выберите объем напитка или введите его числом в чат (в мл):",
        reply_markup=kb
    )
    await state.set_state(OcrState.entering_volume)


@router.callback_query(OcrState.entering_volume, F.data.startswith("ocr_vol_"))
async def choose_volume_predefined_cb(callback: CallbackQuery, state: FSMContext):
    """Пользователь выбрал один из стандартных объемов"""
    volume_ml = int(callback.data.split("_")[-1])
    await state.update_data(volume_ml=volume_ml)
    
    data = await state.get_data()
    drink = data['drink']
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="ocr_confirm_ok")],
        [InlineKeyboardButton(text="✏️ Изменить объем", callback_data="ocr_change_vol")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="ocr_cancel")]
    ])
    
    await callback.message.edit_text(
        f"🥤 Напиток: **{drink['name']}**\n"
        f"📦 Объем: **{volume_ml} мл**\n\n"
        f"Все верно?",
        reply_markup=kb
    )
    await state.set_state(OcrState.confirming_drink)


@router.message(OcrState.entering_volume)
async def custom_volume_input_msg(message: Message, state: FSMContext):
    """Пользователь ввел свой объем текстом"""
    from utils.validators import validate_volume
    volume = validate_volume(message.text)
    
    if volume is None:
        await message.answer("❌ Введите корректный объем в миллилитрах (100 - 10000 мл):")
        return
        
    await state.update_data(volume_ml=volume)
    data = await state.get_data()
    drink = data['drink']
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="ocr_confirm_ok")],
        [InlineKeyboardButton(text="✏️ Изменить объем", callback_data="ocr_change_vol")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="ocr_cancel")]
    ])
    
    await message.answer(
        f"🥤 Напиток: **{drink['name']}**\n"
        f"📦 Объем: **{volume} мл**\n\n"
        f"Все верно?",
        reply_markup=kb
    )
    await state.set_state(OcrState.confirming_drink)


@router.message(OcrState.entering_price)
async def enter_price_save_msg(message: Message, state: FSMContext):
    """Пользователь ввел цену. Записываем покупку в базу"""
    from utils.validators import validate_price
    price = validate_price(message.text)
    
    if price is None:
        await message.answer("❌ Введите корректную цену (0 - 10000 ₽):")
        return
        
    data = await state.get_data()
    drink = data['drink']
    volume_ml = data['volume_ml']
    user_id = message.from_user.id
    
    # 1. Расчет пищевой ценности
    from utils.calculations import calculate_nutrition
    nutrition = calculate_nutrition(
        drink['calories_per_100ml'],
        drink['sugar_per_100ml'],
        drink['caffeine_per_100ml'],
        drink['sodium_per_100ml'],
        volume_ml
    )
    
    try:
        # 2. Сохраняем в Google Sheets и Excel
        await db.add_purchase(
            drink_id=drink['id'],
            user_id=user_id,
            volume_ml=volume_ml,
            price_rub=price,
            calories=nutrition['calories'],
            sugar=nutrition['sugar'],
            caffeine=nutrition['caffeine'],
            sodium=nutrition['sodium'],
            notes="Распознавание по фото"
        )
        
        # 3. Выводим красивое подтверждение
        from utils.formatters import format_purchase_confirmation
        confirmation = format_purchase_confirmation(
            drink['name'],
            volume_ml,
            price,
            nutrition
        )
        await message.answer(confirmation)
        
        # 4. Возврат в основное меню
        await state.clear()
        from handlers.start import get_main_keyboard
        await message.answer("Что дальше?", reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении покупки из фото: {e}")
        await message.answer(f"❌ Ошибка сохранения покупки: {e}")
        await state.clear()


@router.callback_query(F.data == "ocr_cancel")
async def cancel_ocr_cb(callback: CallbackQuery, state: FSMContext):
    """Отмена распознавания"""
    await state.clear()
    await callback.message.delete()
    from handlers.start import get_main_keyboard
    await callback.message.answer("❌ Распознавание фото отменено.", reply_markup=get_main_keyboard())
