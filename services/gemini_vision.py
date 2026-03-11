"""
Сервис для распознавания документов через Gemini Vision API
"""
import google.generativeai as genai
from PIL import Image
from io import BytesIO
import json

from config import GEMINI_API_KEY
from logger import logger


class GeminiVisionService:
    """Сервис для распознавания документов с помощью Gemini Vision"""
    
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("✅ Gemini Vision API инициализирован")
    
    def recognize_invoice(self, photo_bytes):
        """
        Распознать накладную из фотографии
        
        Args:
            photo_bytes: Байты изображения
            
        Returns:
            dict: Распознанные данные в формате:
                {
                    "number": "номер накладной",
                    "date": "дата",
                    "objectName": "название объекта",
                    "contractor": "подрядчик",
                    "items": [{"code": "шифр проекта"}]
                }
                или {"error": "описание ошибки"}
        """
        try:
            # Открываем изображение
            image = Image.open(BytesIO(photo_bytes))
            
            # Промпт для Gemini
            prompt = """Извлеки номер накладной, дату, объект, получателя и список шифров из таблицы. 
Ответ дай только в формате JSON: 
{
    "number": "...", 
    "date": "...", 
    "objectName": "...", 
    "contractor": "...", 
    "items": [{"code": "..."}]
}"""
            
            logger.info("Отправка запроса к Gemini Vision API...")
            
            # Отправляем запрос к Gemini
            response = self.model.generate_content([prompt, image])
            
            # Извлекаем текст ответа
            response_text = response.text.strip()
            
            # Убираем markdown форматирование если есть
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Парсим JSON
            invoice_data = json.loads(response_text)
            
            logger.info(f"✅ Накладная распознана: {invoice_data.get('number', 'б/н')}")
            return invoice_data
        
        except json.JSONDecodeError as e:
            error_msg = f"Ошибка парсинга JSON от Gemini: {e}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        except Exception as e:
            error_msg = f"Ошибка распознавания документа: {e}"
            logger.error(error_msg)
            return {"error": error_msg}


if __name__ == '__main__':
    # Тест инициализации
    try:
        gemini = GeminiVisionService()
        print("✅ Gemini Vision API готов к работе!")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
