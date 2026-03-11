from services.google_sheets import GoogleSheetsService
from config import SHEET_NAMES
import json

sheets_service = GoogleSheetsService()

# Получаем данные из листа 'Численность'
try:
    data = sheets_service.get_values(SHEET_NAMES['HEADCOUNT'])
    print(f'Лист: {SHEET_NAMES["HEADCOUNT"]}')
    print(f'Всего строк: {len(data) if data else 0}')
    
    if data:
        print('\nПервые 3 строки:')
        for i, row in enumerate(data[:3]):
            print(f'Строка {i+1}: {row[:10]}')  # Первые 10 колонок
        
        print('\nПроверка дат в колонке B:')
        for i, row in enumerate(data[2:7], start=3):  # Строки 3-7
            if len(row) > 1 and row[1]:
                print(f'Строка {i}: {row[1]}')
except Exception as e:
    print(f'Ошибка: {e}')
