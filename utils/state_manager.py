"""
Управление состояниями пользователей (Finite State Machine)
"""
import json
from typing import Dict, Any, Optional


class StateManager:
    """Менеджер состояний пользователей"""
    
    def __init__(self):
        # Хранилище состояний в памяти {chat_id: state_dict}
        self._states: Dict[int, Dict[str, Any]] = {}
    
    def get_state(self, chat_id: int) -> Dict[str, Any]:
        """
        Получить состояние пользователя
        
        Args:
            chat_id: ID чата пользователя
            
        Returns:
            dict: Состояние пользователя
        """
        return self._states.get(chat_id, {})
    
    def set_state(self, chat_id: int, state: Dict[str, Any]):
        """
        Установить состояние пользователя
        
        Args:
            chat_id: ID чата
            state: Новое состояние
        """
        self._states[chat_id] = state
    
    def update_state(self, chat_id: int, **kwargs):
        """
        Обновить состояние пользователя
        
        Args:
            chat_id: ID чата
            **kwargs: Поля для обновления
        """
        current_state = self.get_state(chat_id)
        current_state.update(kwargs)
        self._states[chat_id] = current_state
    
    def delete_state(self, chat_id: int):
        """
        Удалить состояние пользователя
        
        Args:
            chat_id: ID чата
        """
        if chat_id in self._states:
            del self._states[chat_id]
    
    def get_mode(self, chat_id: int) -> Optional[str]:
        """
        Получить текущий режим пользователя
        
        Args:
            chat_id: ID чата
            
        Returns:
            str: Режим (headcount, tasks, nsg, questions и т.д.) или None
        """
        state = self.get_state(chat_id)
        return state.get('mode')
    
    def get_step(self, chat_id: int) -> Optional[str]:
        """
        Получить текущий шаг пользователя
        
        Args:
            chat_id: ID чата
            
        Returns:
            str: Шаг или None
        """
        state = self.get_state(chat_id)
        return state.get('step')
    
    def set_mode(self, chat_id: int, mode: str):
        """
        Установить режим пользователя
        
        Args:
            chat_id: ID чата
            mode: Новый режим
        """
        self.update_state(chat_id, mode=mode)
    
    def set_step(self, chat_id: int, step: str):
        """
        Установить шаг пользователя
        
        Args:
            chat_id: ID чата
            step: Новый шаг
        """
        self.update_state(chat_id, step=step)
    
    def clear_all_states(self):
        """Очистить все состояния (для отладки)"""
        self._states.clear()
    
    def get_all_states(self) -> Dict[int, Dict[str, Any]]:
        """Получить все состояния (для отладки)"""
        return self._states.copy()


# Глобальный экземпляр менеджера состояний
state_manager = StateManager()


if __name__ == '__main__':
    # Тест менеджера состояний
    sm = StateManager()
    
    # Установка состояния
    sm.set_state(12345, {'mode': 'headcount', 'step': 'awaiting_number'})
    print(f"State: {sm.get_state(12345)}")
    
    # Обновление состояния
    sm.update_state(12345, org='ООО Подрядчик', shift='День')
    print(f"Updated: {sm.get_state(12345)}")
    
    # Получение режима и шага
    print(f"Mode: {sm.get_mode(12345)}")
    print(f"Step: {sm.get_step(12345)}")
    
    # Удаление состояния
    sm.delete_state(12345)
    print(f"After delete: {sm.get_state(12345)}")
