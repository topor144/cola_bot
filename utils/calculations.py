"""Расчёты пищевой ценности"""

def calculate_nutrition(calories_per_100ml: float, sugar_per_100ml: float, 
                       caffeine_per_100ml: float, sodium_per_100ml: float,
                       volume_ml: int) -> dict:
    """Рассчитать пищевую ценность на реальный объём"""
    multiplier = volume_ml / 100
    
    return {
        "calories": round(calories_per_100ml * multiplier, 1),
        "sugar": round(sugar_per_100ml * multiplier, 1),
        "caffeine": round(caffeine_per_100ml * multiplier, 0),
        "sodium": round(sodium_per_100ml * multiplier, 0),
    }


def format_nutrition(nutrition: dict) -> str:
    """Форматировать пищевую ценность для вывода"""
    return (
        f"🔥 {nutrition['calories']} ккал\n"
        f"🍬 {nutrition['sugar']} г сахара\n"
        f"☕ {nutrition['caffeine']:.0f} мг кофеина\n"
        f"🧂 {nutrition['sodium']:.0f} мг натрия"
    )
