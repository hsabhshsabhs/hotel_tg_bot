"""
Сервис для работы с Google Sheets API
"""
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import (
    GOOGLE_SPREADSHEET_ID,
    GOOGLE_CREDENTIALS_FILE,
    GOOGLE_TOKEN_FILE
)
from logger import logger

# Области доступа для Google Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]


class GoogleSheetsService:
    """Сервис для работы с Google Sheets"""
    
    def __init__(self):
        self.spreadsheet_id = GOOGLE_SPREADSHEET_ID
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Аутентификация в Google API"""
        creds = None
        
        # Загрузка сохраненных учетных данных
        if os.path.exists(GOOGLE_TOKEN_FILE):
            try:
                with open(GOOGLE_TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                logger.warning(f"Не удалось загрузить token.pickle: {e}. Удаляю битый файл.")
                try:
                    os.remove(GOOGLE_TOKEN_FILE)
                except:
                    pass
                creds = None
        
        # Если нет валидных учетных данных, запрашиваем авторизацию
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Обновление токена Google API...")
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Ошибка при обновлении токена: {e}. Требуется повторная авторизация.")
                    creds = None
            
            if not creds or not creds.valid:
                if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
                    logger.warning(f"Файл {GOOGLE_CREDENTIALS_FILE} не найден. Google Sheets отключен.")
                    self.service = None
                    return
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        GOOGLE_CREDENTIALS_FILE, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.warning(f"Не удалось пройти авторизацию Google: {e}. Google Sheets отключен.")
                    self.service = None
                    return
            
            try:
                with open(GOOGLE_TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info("Токен Google API сохранен")
            except Exception as e:
                logger.warning(f"Не удалось сохранить токен: {e}")
        
        try:
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("✅ Подключение к Google Sheets успешно")
        except HttpError as error:
            logger.error(f"Ошибка подключения к Google Sheets: {error}")
            self.service = None
    
    def get_values(self, sheet_name, range_notation='A:Z'):
        """
        Получить значения из листа
        
        Args:
            sheet_name: Название листа
            range_notation: Диапазон ячеек (например, 'A:Z' или 'A1:D10')
            
        Returns:
            list: Список строк с данными
        """
        if self.service is None:
            logger.warning(f"Google Sheets отключен. Возвращаю пустой список для {sheet_name}.")
            return []
        try:
            range_name = f"{sheet_name}!{range_notation}"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            logger.debug(f"Получено {len(values)} строк из {sheet_name}")
            return values
        
        except HttpError as error:
            logger.error(f"Ошибка чтения из {sheet_name}: {error}")
            return []
    
    def update_cell(self, sheet_name, cell, value):
        """
        Обновить значение одной ячейки
        
        Args:
            sheet_name: Название листа
            cell: Адрес ячейки (например, 'A1')
            value: Новое значение
        """
        try:
            range_name = f"{sheet_name}!{cell}"
            body = {'values': [[value]]}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logger.debug(f"Обновлена ячейка {cell} в {sheet_name}")
        
        except HttpError as error:
            logger.error(f"Ошибка обновления ячейки {cell} в {sheet_name}: {error}")
            raise
    
    def update_range(self, sheet_name, range_notation, values):
        """
        Обновить диапазон ячеек
        
        Args:
            sheet_name: Название листа
            range_notation: Диапазон (например, 'A1:D5')
            values: Двумерный массив значений
        """
        try:
            range_name = f"{sheet_name}!{range_notation}"
            body = {'values': values}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logger.debug(f"Обновлен диапазон {range_notation} в {sheet_name}")
        
        except HttpError as error:
            logger.error(f"Ошибка обновления диапазона в {sheet_name}: {error}")
            raise
    
    def append_row(self, sheet_name, values):
        """
        Добавить строку в конец листа
        
        Args:
            sheet_name: Название листа
            values: Список значений для новой строки
        """
        try:
            range_name = f"{sheet_name}!A:Z"
            body = {'values': [values]}
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.debug(f"Добавлена строка в {sheet_name}")
        
        except HttpError as error:
            logger.error(f"Ошибка добавления строки в {sheet_name}: {error}")
            raise
    
    def find_row_by_value(self, sheet_name, column_index, search_value):
        """
        Найти строку по значению в определенной колонке
        
        Args:
            sheet_name: Название листа
            column_index: Индекс колонки (0-based)
            search_value: Искомое значение
            
        Returns:
            tuple: (row_index, row_data) или (None, None) если не найдено
        """
        values = self.get_values(sheet_name)
        
        for i, row in enumerate(values):
            if len(row) > column_index and str(row[column_index]) == str(search_value):
                return (i, row)
        
        return (None, None)
    
    def get_spreadsheet_timezone(self):
        """Получить часовой пояс таблицы"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            timezone = spreadsheet.get('properties', {}).get('timeZone', 'UTC')
            return timezone
        
        except HttpError as error:
            logger.error(f"Ошибка получения timezone: {error}")
            return 'UTC'


if __name__ == '__main__':
    # Тест подключения
    try:
        sheets = GoogleSheetsService()
        timezone = sheets.get_spreadsheet_timezone()
        print(f"✅ Подключение к Google Sheets успешно!")
        print(f"   Spreadsheet ID: {GOOGLE_SPREADSHEET_ID}")
        print(f"   Timezone: {timezone}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
