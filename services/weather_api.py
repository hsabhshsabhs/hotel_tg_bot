"""
Сервис для получения прогноза погоды через OpenWeatherMap API
"""
import requests
from datetime import datetime

from config import OPENWEATHER_API_KEY, WEATHER_CITY, WEATHER_LANG, WEATHER_UNITS
from logger import logger


class WeatherService:
    """Сервис для получения прогноза погоды"""
    
    def __init__(self):
        self.api_key = OPENWEATHER_API_KEY
        self.city = WEATHER_CITY
        self.lang = WEATHER_LANG
        self.units = WEATHER_UNITS
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def get_current_weather(self):
        """
        Получить текущую погоду
        
        Returns:
            str: Форматированное сообщение с прогнозом или сообщение об ошибке
        """
        try:
            url = f"{self.base_url}/weather"
            params = {
                'q': self.city,
                'appid': self.api_key,
                'lang': self.lang,
                'units': self.units
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Форматируем сообщение
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            description = data['weather'][0]['description'].capitalize()
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            
            message = f"🌤 <b>Погода в {self.city}</b>\n\n"
            message += f"🌡 Температура: <b>{temp:.1f}°C</b>\n"
            message += f"🤔 Ощущается как: {feels_like:.1f}°C\n"
            message += f"☁️ {description}\n"
            message += f"💧 Влажность: {humidity}%\n"
            message += f"💨 Ветер: {wind_speed} м/с"
            
            logger.info(f"Получена текущая погода для {self.city}")
            return message
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка получения погоды: {e}")
            return "❌ Не удалось получить данные о погоде. Попробуйте позже."
    
    def get_forecast(self, days=7):
        """
        Получить прогноз погоды на несколько дней
        
        Args:
            days: Количество дней (максимум 7)
            
        Returns:
            str: Форматированное сообщение с прогнозом
        """
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'q': self.city,
                'appid': self.api_key,
                'lang': self.lang,
                'units': self.units,
                'cnt': min(days * 8, 40)  # API возвращает данные каждые 3 часа
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Группируем по дням
            daily_forecasts = {}
            for item in data['list']:
                dt = datetime.fromtimestamp(item['dt'])
                date_key = dt.strftime('%Y-%m-%d')
                
                if date_key not in daily_forecasts:
                    daily_forecasts[date_key] = {
                        'temps': [],
                        'descriptions': [],
                        'date': dt
                    }
                
                daily_forecasts[date_key]['temps'].append(item['main']['temp'])
                daily_forecasts[date_key]['descriptions'].append(
                    item['weather'][0]['description']
                )
            
            # Форматируем сообщение
            message = f"📅 <b>Прогноз погоды на неделю ({self.city})</b>\n\n"
            
            for date_key in sorted(daily_forecasts.keys())[:days]:
                forecast = daily_forecasts[date_key]
                date_str = forecast['date'].strftime('%d.%m (%a)')
                
                min_temp = min(forecast['temps'])
                max_temp = max(forecast['temps'])
                
                # Берем самое частое описание
                description = max(set(forecast['descriptions']), 
                                key=forecast['descriptions'].count)
                
                message += f"<b>{date_str}</b>: {min_temp:.0f}°..{max_temp:.0f}°C, {description}\n"
            
            logger.info(f"Получен прогноз погоды на {days} дней для {self.city}")
            return message
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка получения прогноза: {e}")
            return "❌ Не удалось получить прогноз погоды. Попробуйте позже."


if __name__ == '__main__':
    # Тест сервиса
    try:
        weather = WeatherService()
        print("Текущая погода:")
        print(weather.get_current_weather())
        print("\nПрогноз на неделю:")
        print(weather.get_forecast())
    except Exception as e:
        print(f"❌ Ошибка: {e}")
