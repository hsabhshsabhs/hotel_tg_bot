"""
Логирование для бота
"""
import logging
import os
from datetime import datetime
from config import LOG_LEVEL, LOG_TO_FILE, LOG_TO_CONSOLE, LOG_FILE

def setup_logger(name='hotel_bot'):
    """
    Настройка логгера для бота
    
    Args:
        name: Имя логгера
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
    
    # Очистка существующих обработчиков
    logger.handlers.clear()
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Логирование в консоль
    if LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Логирование в файл
    if LOG_TO_FILE:
        # Создаем директорию logs если её нет
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Создаем основной логгер
logger = setup_logger()

def log_to_sheet(level, message):
    """
    Логирование в Google Sheets (аналог logToSheet из оригинального бота)
    
    Args:
        level: Уровень лога (INFO, ERROR, WARN)
        message: Сообщение для логирования
    """
    try:
        from services.google_sheets import GoogleSheetsService
        from config import SHEET_NAMES
        
        sheets_service = GoogleSheetsService()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sheets_service.append_row(
            SHEET_NAMES['LOGS'],
            [timestamp, level, message]
        )
    except Exception as e:
        # Если не удалось записать в Sheets, пишем в обычный лог
        logger.error(f"Failed to log to sheet: {e}. Original log: [{level}] {message}")

if __name__ == '__main__':
    # Тест логирования
    logger.info("Тест логирования - INFO")
    logger.warning("Тест логирования - WARNING")
    logger.error("Тест логирования - ERROR")
    print(f"✅ Логи записаны в {LOG_FILE if LOG_TO_FILE else 'консоль'}")
