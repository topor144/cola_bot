"""Форматирование сообщений"""

from datetime import datetime


def format_purchase_confirmation(drink_name: str, volume_ml: int, price: float,
                                nutrition: dict) -> str:
    """Форматировать подтверждение покупки"""
    return (
        f"✅ Покупка записана!\n\n"
        f"🥤 {drink_name}\n"
        f"📦 {volume_ml} мл\n"
        f"💰 {price} ₽\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Пищевая ценность:\n"
        f"🔥 {nutrition['calories']} ккал\n"
        f"🍬 {nutrition['sugar']} г сахара\n"
        f"☕ {nutrition['caffeine']:.0f} мг кофеина\n"
        f"🧂 {nutrition['sodium']:.0f} мг натрия"
    )


def format_drink_list(drinks: list) -> str:
    """Форматировать список напитков"""
    if not drinks:
        return "❌ Напитки не добавлены"
    
    text = "📋 Ваши напитки:\n\n"
    for drink in drinks:
        text += (
            f"🥤 {drink['name']}\n"
            f"   📦 По умолчанию: {drink.get('volume_default', 2000)} мл\n"
            f"   🔥 Калории: {drink['calories_per_100ml']} ккал/100мл\n"
            f"   🍬 Сахар: {drink['sugar_per_100ml']}г/100мл\n\n"
        )
    return text.strip()


def format_history(purchases: list) -> str:
    """Форматировать историю покупок"""
    if not purchases:
        return "❌ Покупок нет"
    
    text = "📋 История покупок:\n\n"
    for idx, p in enumerate(purchases, 1):
        drink_name = p.get('drinks', {}).get('name', 'Неизвестно') if isinstance(p.get('drinks'), dict) else p.get('drink_id')
        text += (
            f"{idx}. 🥤 {drink_name}\n"
            f"   📦 {p['volume_ml']} мл\n"
            f"   💰 {p.get('price_rub', 0)} ₽\n"
            f"   📅 {p['purchase_date']}\n"
            f"   🔥 {p.get('calories_total', 0):.0f} ккал\n\n"
        )
    return text.strip()


def format_stats(stats: dict) -> str:
    """Форматировать статистику"""
    if not stats or stats.get('total_purchases', 0) == 0:
        return "❌ Нет данных для статистики"
    
    avg_price = stats['total_spent'] / stats['total_purchases'] if stats['total_purchases'] > 0 else 0
    total_liters = stats['total_volume'] / 1000
    
    return (
        f"📊 Статистика за последний месяц\n\n"
        f"📈 Всего покупок: {stats['total_purchases']}\n"
        f"💰 Потрачено: {stats['total_spent']:.0f} ₽\n"
        f"💵 Средняя цена: {avg_price:.0f} ₽\n\n"
        f"📦 Всего выпито: {total_liters:.1f} л\n"
        f"🔥 Всего калорий: {stats['total_calories']:.0f} ккал\n"
        f"🍬 Всего сахара: {stats['total_sugar']:.0f} г\n"
        f"☕ Всего кофеина: {stats['total_caffeine']:.0f} мг\n"
        f"🧂 Всего натрия: {stats['total_sodium']:.0f} мг"
    )
