"""
Сервис для работы с Google Drive API
"""
import os
from google.auth import default
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO

from config import (
    GOOGLE_DRIVE_FOLDER_ID,
    GOOGLE_CREDENTIALS_FILE,
)
from logger import logger

SCOPES = [
    'https://www.googleapis.com/auth/drive.file'
]


class GoogleDriveService:
    """Сервис для работы с Google Drive"""
    
    def __init__(self):
        self.folder_id = GOOGLE_DRIVE_FOLDER_ID
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Аутентификация в Google API через Service Account или ADC"""
        creds = None
        
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') or GOOGLE_CREDENTIALS_FILE
        
        if os.path.exists(creds_path):
            try:
                creds = service_account.Credentials.from_service_account_file(
                    creds_path, scopes=SCOPES
                )
                logger.info("✅ Google Drive: Service Account авторизация успешна")
            except Exception as e:
                logger.warning(f"Не удалось загрузить Service Account: {e}")
                creds = None
        
        if not creds:
            try:
                creds, _ = default(scopes=SCOPES)
                logger.info("✅ Google Drive: ADC авторизация успешна")
            except Exception as e:
                logger.warning(f"Не удалось пройти авторизацию Google: {e}. Google Drive отключён.")
                self.service = None
                return
        
        try:
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("✅ Подключение к Google Drive успешно")
        except HttpError as error:
            logger.error(f"Ошибка подключения к Google Drive: {error}")
            self.service = None
    
    def upload_photo(self, photo_bytes, filename):
        """Загрузить фото в Google Drive"""
        if not self.service:
            logger.warning("Google Drive отключён, фото не загружено")
            return None
        
        try:
            media = MediaIoBaseUpload(
                BytesIO(photo_bytes),
                mimetype='image/jpeg',
                resumable=True
            )
            
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id]
            }
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            
            self.service.permissions().create(
                fileId=file_id,
                body={
                    'type': 'anyone',
                    'role': 'reader'
                }
            ).execute()
            
            photo_url = f"https://drive.google.com/uc?id={file_id}"
            
            logger.info(f"Фото загружено: {filename} -> {photo_url}")
            return photo_url
        
        except HttpError as error:
            logger.error(f"Ошибка загрузки фото в Drive: {error}")
            return None
    
    def delete_file(self, file_id):
        """Удалить файл из Google Drive"""
        if not self.service:
            logger.warning("Google Drive отключён, файл не удален")
            return
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Файл {file_id} удален из Drive")
        except HttpError as error:
            logger.error(f"Ошибка удаления файла {file_id}: {error}")


if __name__ == '__main__':
    try:
        drive = GoogleDriveService()
        print(f"✅ Подключение к Google Drive успешно!")
        print(f"   Folder ID: {GOOGLE_DRIVE_FOLDER_ID}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
