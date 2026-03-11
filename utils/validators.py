"""
Утилиты для валидации данных
"""
from datetime import datetime
import re


def is_valid_date(date_string):
    """
    Проверка валидности даты в формате DD.MM.YYYY
    
    Args:
        date_string: Строка с датой
        
    Returns:
        dict: {"isValid": bool, "errorMessage": str}
    """
    if not date_string:
        return {
            "isValid": False,
            "errorMessage": "❌ Дата не может быть пустой."
        }
    
    # Проверка формата
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', date_string):
        return {
            "isValid": False,
            "errorMessage": "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ (например, 01.12.2025)"
        }
    
    # Проверка валидности даты
    try:
        day, month, year = map(int, date_string.split('.'))
        datetime(year, month, day)
        
        return {
            "isValid": True,
            "errorMessage": ""
        }
    except ValueError:
        return {
            "isValid": False,
            "errorMessage": "❌ Указана несуществующая дата. Проверьте правильность ввода."
        }


def is_valid_number(value):
    """
    Проверка, является ли значение числом
    
    Args:
        value: Значение для проверки
        
    Returns:
        bool: True если число, False иначе
    """
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def is_valid_telegram_id(telegram_id):
    """
    Проверка валидности Telegram ID
    
    Args:
        telegram_id: ID пользователя
        
    Returns:
        bool: True если валидный, False иначе
    """
    try:
        return isinstance(telegram_id, int) or (
            isinstance(telegram_id, str) and telegram_id.isdigit()
        )
    except:
        return False


def sanitize_input(text, max_length=1000):
    """
    Очистка пользовательского ввода
    
    Args:
        text: Текст для очистки
        max_length: Максимальная длина
        
    Returns:
        str: Очищенный текст
    """
    if not text:
        return ""
    
    # Убираем лишние пробелы
    text = ' '.join(text.split())
    
    # Ограничиваем длину
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


if __name__ == '__main__':
    # Тесты
    print("Тест валидации дат:")
    print(is_valid_date("01.12.2025"))  # Valid
    print(is_valid_date("32.13.2025"))  # Invalid
    print(is_valid_date("01-12-2025"))  # Invalid format
    
    print("\nТест валидации чисел:")
    print(is_valid_number("123"))       # True
    print(is_valid_number("12.5"))      # True
    print(is_valid_number("abc"))       # False
