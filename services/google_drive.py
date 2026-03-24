"""
Сервис для работы с Google Drive API
"""
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO

from config import (
    GOOGLE_DRIVE_FOLDER_ID,
    GOOGLE_CREDENTIALS_FILE,
    GOOGLE_TOKEN_FILE
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
        """Аутентификация в Google API"""
        creds = None
        
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
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Обновление токена Google Drive API...")
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Ошибка при обновлении токена Drive: {e}. Требуется повторная авторизация.")
                    creds = None
            
            if not creds or not creds.valid:
                if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
                    logger.warning("credentials.json не найден. Google Drive отключён.")
                    return
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        GOOGLE_CREDENTIALS_FILE, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    with open(GOOGLE_TOKEN_FILE, 'wb') as token:
                        pickle.dump(creds, token)
                except Exception as e:
                    logger.warning(f"Не удалось пройти авторизацию Google: {e}. Google Drive отключён.")
                    return
        
        try:
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("✅ Подключение к Google Drive успешно")
        except HttpError as error:
            logger.error(f"Ошибка подключения к Google Drive: {error}")
            self.service = None
    
    def upload_photo(self, photo_bytes, filename):
        """
        Загрузить фото в Google Drive
        
        Args:
            photo_bytes: Байты изображения
            filename: Имя файла
            
        Returns:
            str: URL для просмотра файла или None при ошибке
        """
        if not self.service:
            logger.warning("Google Drive отключён, фото не загружено")
            return None
        
        try:
            # Создаем медиа-объект из байтов
            media = MediaIoBaseUpload(
                BytesIO(photo_bytes),
                mimetype='image/jpeg',
                resumable=True
            )
            
            # Метаданные файла
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id]
            }
            
            # Загружаем файл
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            
            # Делаем файл доступным по ссылке
            self.service.permissions().create(
                fileId=file_id,
                body={
                    'type': 'anyone',
                    'role': 'reader'
                }
            ).execute()
            
            # Формируем URL для просмотра
            photo_url = f"https://drive.google.com/uc?id={file_id}"
            
            logger.info(f"Фото загружено: {filename} -> {photo_url}")
            return photo_url
        
        except HttpError as error:
            logger.error(f"Ошибка загрузки фото в Drive: {error}")
            return None
    
    def delete_file(self, file_id):
        """
        Удалить файл из Google Drive
        
        Args:
            file_id: ID файла
        """
        if not self.service:
            logger.warning("Google Drive отключён, файл не удален")
            return
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Файл {file_id} удален из Drive")
        except HttpError as error:
            logger.error(f"Ошибка удаления файла {file_id}: {error}")


if __name__ == '__main__':
    # Тест подключения
    try:
        drive = GoogleDriveService()
        print(f"✅ Подключение к Google Drive успешно!")
        print(f"   Folder ID: {GOOGLE_DRIVE_FOLDER_ID}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
