"""Валидация входных данных"""

def validate_number(text: str, min_val: float = 0, max_val: float = 99999) -> float | None:
    """Валидировать число"""
    try:
        value = float(text)
        if min_val <= value <= max_val:
            return value
        return None
    except ValueError:
        return None


def validate_int(text: str, min_val: int = 0, max_val: int = 99999) -> int | None:
    """Валидировать целое число"""
    try:
        value = int(text)
        if min_val <= value <= max_val:
            return value
        return None
    except ValueError:
        return None


def validate_drink_name(name: str) -> str | None:
    """Валидировать название напитка"""
    name = name.strip()
    if len(name) < 2 or len(name) > 100:
        return None
    return name


def validate_price(text: str) -> float | None:
    """Валидировать цену"""
    return validate_number(text, min_val=0, max_val=10000)


def validate_volume(text: str) -> int | None:
    """Валидировать объём"""
    return validate_int(text, min_val=100, max_val=10000)


def validate_nutrition_value(text: str) -> float | None:
    """Валидировать значение пищевой ценности"""
    return validate_number(text, min_val=0, max_val=1000)
