"""
Сервис для работы с Google Sheets API
"""
import os
from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import (
    GOOGLE_SPREADSHEET_ID,
    GOOGLE_CREDENTIALS_FILE,
)
from logger import logger

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
        """Аутентификация в Google API через Service Account или ADC"""
        creds = None
        
        # Render stores secret files at /etc/secrets/<filename>
        possible_paths = ['/etc/secrets/service_account.json']
        if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
            possible_paths.insert(0, os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
        possible_paths.append(GOOGLE_CREDENTIALS_FILE)
        
        for creds_path in possible_paths:
            if os.path.exists(creds_path):
                try:
                    from google.oauth2 import service_account
                    creds = service_account.Credentials.from_service_account_file(
                        creds_path, scopes=SCOPES
                    )
                    logger.info("✅ Google Sheets: Service Account авторизация успешна")
                    break
                except Exception as e:
                    logger.warning(f"Не удалось загрузить Service Account: {e}")
                    creds = None
                    continue
            if creds:
                break
        
        if not creds:
            try:
                creds, _ = default(scopes=SCOPES)
                logger.info("✅ Google Sheets: ADC авторизация успешна")
            except Exception as e:
                logger.warning(f"Не удалось пройти авторизацию Google: {e}. Google Sheets отключён.")
                self.service = None
                return
        
        try:
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("✅ Подключение к Google Sheets успешно")
        except HttpError as error:
            logger.error(f"Ошибка подключения к Google Sheets: {error}")
            self.service = None
    
    def get_values(self, sheet_name, range_notation='A:ZZ'):
        """Получить значения из листа"""
        if not self.service:
            logger.warning(f"Google Sheets отключён, get_values пропущен")
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
        """Обновить значение одной ячейки"""
        if not self.service:
            logger.warning(f"Google Sheets отключён, update_cell пропущен")
            return
        
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
        """Обновить диапазон ячеек"""
        if not self.service:
            logger.warning(f"Google Sheets отключён, update_range пропущен")
            return
        
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
        """Добавить строку в конец листа"""
        if not self.service:
            logger.warning(f"Google Sheets отключён, append_row пропущен")
            return
        
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
        """Найти строку по значению в определенной колонке"""
        values = self.get_values(sheet_name)
        
        for i, row in enumerate(values):
            if len(row) > column_index and str(row[column_index]) == str(search_value):
                return (i, row)
        
        return (None, None)
    
    def get_spreadsheet_timezone(self):
        """Получить часовой пояс таблицы"""
        if not self.service:
            return 'UTC'
        
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
    try:
        sheets = GoogleSheetsService()
        timezone = sheets.get_spreadsheet_timezone()
        print(f"✅ Подключение к Google Sheets успешно!")
        print(f"   Spreadsheet ID: {GOOGLE_SPREADSHEET_ID}")
        print(f"   Timezone: {timezone}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
