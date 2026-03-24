"""
Конфигурация бота для управления строительством отеля
"""
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

GOOGLE_SPREADSHEET_ID = os.getenv('GOOGLE_SPREADSHEET_ID')
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '1FHAPQWiQyhe-H45Iv_uDzNdmNJC5Bp5g')

# Service Account JSON или путь к credentials.json
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials/service_account.json')
GOOGLE_TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'credentials/token.json')

SHEET_NAMES = {
    'COMPLEX_QUESTIONS': os.getenv('SHEET_NAME_COMPLEX_QUESTIONS', 'Вопросы к комплексу'),
    'HEADCOUNT': os.getenv('SHEET_NAME_HEADCOUNT', 'Численность'),
    'HEADCOUNT_EXTENDED': os.getenv('SHEET_NAME_HEADCOUNT_EXTENDED', 'Численность расширенная'),

# ID группы для отправки сводок
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID', '-3486618308')),
    'HEADCOUNT_EXTENDED': os.getenv('SHEET_NAME_HEADCOUNT_EXTENDED', 'Численность расширенная'),
    'TASKS': os.getenv('SHEET_NAME_TASKS', 'Целевые задания'),
    'ACCESS': os.getenv('SHEET_NAME_ACCESS', 'Доступ'),
    'QUESTIONS': os.getenv('SHEET_NAME_QUESTIONS', 'Вопросы к заказчику'),
    'NSG': os.getenv('SHEET_NAME_NSG', 'НСЗ'),
    'COMPLEX_PROTOCOL': os.getenv('SHEET_NAME_COMPLEX_PROTOCOL', 'Протокол комплекса строительства'),
    'PSD_LOG': os.getenv('SHEET_NAME_PSD_LOG', 'БД журнал ПСД'),
    'LOGS': os.getenv('SHEET_NAME_LOGS', 'logsbot'),
}

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_PROJECT_ID = os.getenv('GEMINI_PROJECT_ID', 'gen-lang-client-0978272443')

OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
WEATHER_CITY = os.getenv('WEATHER_CITY', 'Moscow')
WEATHER_LANG = os.getenv('WEATHER_LANG', 'ru')
WEATHER_UNITS = 'metric'

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'true').lower() == 'true'
LOG_TO_CONSOLE = os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true'
LOG_FILE = 'logs/bot.log'

REMINDER_DAY_CONTRACTORS = '08:00'
REMINDER_NIGHT_CONTRACTORS = '20:00'
REMINDER_DAY_ENGINEERS = '09:00'
REMINDER_NIGHT_ENGINEERS = '21:00'

ROLE_ENGINEER = 'ИНЖЕНЕР'
ROLE_CONTRACTOR = 'ПОДРЯДЧИК'

# =================================================================
# SCHEDULER
# =================================================================
HEADCOUNT_SUMMARY_TIMES = os.getenv('HEADCOUNT_SUMMARY_TIMES', '09:00,09:30,10:00')

def validate_config():
    """Проверка наличия обязательных параметров конфигурации"""
    errors = []
    
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN не установлен")
    
    if not GOOGLE_SPREADSHEET_ID:
        errors.append("GOOGLE_SPREADSHEET_ID не установлен")
    
    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY не установлен (требуется для распознавания документов)")
    
    if not OPENWEATHER_API_KEY:
        errors.append("OPENWEATHER_API_KEY не установлен (требуется для модуля погоды)")
    
    if errors:
        error_msg = "\n".join(f"  - {err}" for err in errors)
        raise ValueError(f"Ошибки конфигурации:\n{error_msg}")
    
    return True

if __name__ == '__main__':
    try:
        validate_config()
        print("✅ Конфигурация валидна!")
    except ValueError as e:
        print(f"❌ {e}")
