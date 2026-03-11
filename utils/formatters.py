"""
Утилиты для форматирования сообщений
"""
from datetime import datetime


def format_date(date_obj, timezone='Europe/Moscow'):
    """
    Форматировать дату в DD.MM.YYYY
    
    Args:
        date_obj: Объект datetime
        timezone: Часовой пояс
        
    Returns:
        str: Отформатированная дата
    """
    if isinstance(date_obj, str):
        return date_obj
    
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%d.%m.%Y')
    
    return str(date_obj)


def format_datetime(dt_obj):
    """
    Форматировать дату и время
    
    Args:
        dt_obj: Объект datetime
        
    Returns:
        str: Отформатированная дата и время
    """
    if isinstance(dt_obj, datetime):
        return dt_obj.strftime('%d.%m.%Y %H:%M:%S')
    
    return str(dt_obj)


def escape_html(text):
    """
    Экранировать HTML символы для Telegram
    
    Args:
        text: Текст для экранирования
        
    Returns:
        str: Экранированный текст
    """
    if not text:
        return ""
    
    text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    return text


def format_task_message(task_data):
    """
    Форматировать сообщение о задании
    
    Args:
        task_data: Словарь с данными задания
        
    Returns:
        str: Отформатированное сообщение
    """
    message = f"<b>Задание №{task_data.get('number', '?')}</b>\n\n"
    message += f"<b>Подрядчик:</b> {escape_html(task_data.get('contractor', ''))}\n"
    message += f"<b>Текст задания:</b> {escape_html(task_data.get('text', ''))}\n"
    
    if task_data.get('photo_link'):
        message += f"<b>Фото к заданию:</b> <a href=\"{task_data['photo_link']}\">Посмотреть</a>\n"
    
    if task_data.get('deadline'):
        message += f"<b>Срок:</b> {format_date(task_data['deadline'])}\n"
    
    if task_data.get('status'):
        message += f"<b>Статус:</b> {task_data['status']}\n"
    
    return message


def format_headcount_summary(today_data, monthly_data):
    """
    Форматировать сводку по численности
    
    Args:
        today_data: Данные за сегодня {day: int, night: int, total: int, date: str}
        monthly_data: Список месячных данных [{name: str, average: float}]
        
    Returns:
        str: Отформатированное сообщение
    """
    message = "📊 <b>Сводка по численности персонала</b>\n\n"
    
    message += f"<b><u>Данные за сегодня ({today_data['date']}):</u></b>\n"
    message += f"☀️ Дневная смена: <b>{today_data['day']} чел.</b>\n"
    message += f"🌙 Ночная смена: <b>{today_data['night']} чел.</b>\n"
    message += f"📈 <b>Всего за сутки: {today_data['total']} чел.</b>\n\n"
    
    if monthly_data:
        message += "<b><u>Среднемесячная численность:</u></b>\n"
        for month in monthly_data:
            message += f"{month['name']} - <b>{month['average']} чел.</b>\n"
    
    return message


def truncate_text(text, max_length=50, suffix='...'):
    """
    Обрезать текст до максимальной длины
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина
        suffix: Суффикс для обрезанного текста
        
    Returns:
        str: Обрезанный текст
    """
    if not text:
        return ""
    
    text = str(text)
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


if __name__ == '__main__':
    # Тесты
    print("Тест форматирования даты:")
    print(format_date(datetime.now()))
    
    print("\nТест экранирования HTML:")
    print(escape_html("<script>alert('test')</script>"))
    
    print("\nТест обрезки текста:")
    print(truncate_text("Очень длинный текст который нужно обрезать", 20))
