"""
Утилиты для авторизации и проверки ролей пользователей
"""
from typing import Optional
from services.google_sheets import GoogleSheetsService
from config import SHEET_NAMES, ROLE_ENGINEER, ROLE_CONTRACTOR
from logger import logger


class AuthService:
    """Сервис авторизации и управления ролями"""
    
    def __init__(self):
        self.sheets_service = GoogleSheetsService()
        self._access_cache = {}  # Кэш для ускорения проверок
    
    def get_user_role(self, chat_id: int) -> str:
        """
        Получить роль пользователя
        
        Args:
            chat_id: Telegram ID пользователя
            
        Returns:
            str: ROLE_ENGINEER или ROLE_CONTRACTOR
        """
        try:
            # Проверяем кэш
            if chat_id in self._access_cache:
                return self._access_cache[chat_id]
            
            # Получаем данные из листа "Доступ"
            access_data = self.sheets_service.get_values(
                SHEET_NAMES['ACCESS'],
                'B:B'  # Колонка B содержит Telegram ID инженеров
            )
            
            # Проверяем, есть ли chat_id в списке инженеров
            telegram_ids = [str(row[0]) for row in access_data if row]
            
            if str(chat_id) in telegram_ids:
                role = ROLE_ENGINEER
            else:
                role = ROLE_CONTRACTOR
            
            # Сохраняем в кэш
            self._access_cache[chat_id] = role
            
            logger.debug(f"User {chat_id} role: {role}")
            return role
        
        except Exception as e:
            logger.error(f"Ошибка получения роли пользователя {chat_id}: {e}")
            return ROLE_CONTRACTOR  # По умолчанию подрядчик
    
    def is_engineer(self, chat_id: int) -> bool:
        """
        Проверить, является ли пользователь инженером
        
        Args:
            chat_id: Telegram ID
            
        Returns:
            bool: True если инженер
        """
        return self.get_user_role(chat_id) == ROLE_ENGINEER
    
    def is_contractor(self, chat_id: int) -> bool:
        """
        Проверить, является ли пользователь подрядчиком
        
        Args:
            chat_id: Telegram ID
            
        Returns:
            bool: True если подрядчик
        """
        return self.get_user_role(chat_id) == ROLE_CONTRACTOR
    
    def get_engineer_name(self, chat_id: int) -> Optional[str]:
        """
        Получить имя инженера по его Telegram ID
        
        Args:
            chat_id: Telegram ID
            
        Returns:
            str: Имя инженера или None
        """
        try:
            access_data = self.sheets_service.get_values(
                SHEET_NAMES['ACCESS'],
                'A:B'  # A - имя, B - Telegram ID
            )
            
            for row in access_data[1:]:  # Пропускаем заголовок
                if len(row) >= 2 and str(row[1]) == str(chat_id):
                    return row[0]
            
            return None
        
        except Exception as e:
            logger.error(f"Ошибка получения имени инженера {chat_id}: {e}")
            return None
    
    def get_contractor_info(self, chat_id: int) -> Optional[dict]:
        """
        Получить информацию о подрядчике
        
        Args:
            chat_id: Telegram ID
            
        Returns:
            dict: {"name": str, "direction": str} или None
        """
        try:
            access_data = self.sheets_service.get_values(
                SHEET_NAMES['ACCESS'],
                'C:E'  # C - организация, D - направление, E - Telegram IDs
            )
            
            for row in access_data[1:]:  # Пропускаем заголовок
                if len(row) >= 3:
                    telegram_ids = str(row[2]).split(',')
                    telegram_ids = [tid.strip() for tid in telegram_ids]
                    
                    if str(chat_id) in telegram_ids:
                        return {
                            "name": row[0],
                            "direction": row[1] if len(row) > 1 else ""
                        }
            
            return None
        
        except Exception as e:
            logger.error(f"Ошибка получения информации о подрядчике {chat_id}: {e}")
            return None
    
    def get_all_engineers(self) -> list:
        """
        Получить список всех Telegram ID инженеров
        
        Returns:
            list: Список ID инженеров
        """
        try:
            access_data = self.sheets_service.get_values(
                SHEET_NAMES['ACCESS'],
                'B:B'
            )
            
            engineer_ids = []
            for row in access_data[1:]:  # Пропускаем заголовок
                if row and row[0]:
                    # Может быть несколько ID через запятую
                    ids = str(row[0]).split(',')
                    engineer_ids.extend([tid.strip() for tid in ids if tid.strip()])
            
            return engineer_ids
        
        except Exception as e:
            logger.error(f"Ошибка получения списка инженеров: {e}")
            return []
    
    def get_contractors_list(self) -> list:
        """
        Получить список всех подрядчиков
        
        Returns:
            list: Список названий организаций
        """
        try:
            access_data = self.sheets_service.get_values(
                SHEET_NAMES['ACCESS'],
                'C:C'  # Колонка с названиями организаций
            )
            
            contractors = []
            for row in access_data[1:]:  # Пропускаем заголовок
                if row and row[0]:
                    contractors.append(row[0])
            
            # Убираем дубликаты и сортируем
            contractors = sorted(list(set(contractors)))
            
            return contractors
        
        except Exception as e:
            logger.error(f"Ошибка получения списка подрядчиков: {e}")
            return []
    
    def clear_cache(self):
        """Очистить кэш ролей (для обновления после изменений в таблице)"""
        self._access_cache.clear()
        logger.info("Кэш ролей очищен")


# Глобальный экземпляр сервиса авторизации
auth_service = AuthService()


if __name__ == '__main__':
    # Тест сервиса авторизации
    try:
        auth = AuthService()
        
        # Получить список подрядчиков
        contractors = auth.get_contractors_list()
        print(f"Подрядчики: {contractors}")
        
        # Получить список инженеров
        engineers = auth.get_all_engineers()
        print(f"Инженеры: {engineers}")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
