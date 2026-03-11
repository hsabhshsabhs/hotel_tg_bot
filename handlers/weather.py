"""
Обработчик модуля "Погода"
"""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from services.weather_api import WeatherService
from utils.state_manager import state_manager
from logger import logger

weather_service = WeatherService()


async def show_weather_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню погоды"""
    chat_id = update.effective_chat.id
    
    state_manager.set_mode(chat_id, 'weather')
    
    keyboard = [
        [
            InlineKeyboardButton("🌤 Сегодня", callback_data="weather_today"),
            InlineKeyboardButton("📅 На неделю", callback_data="weather_week")
        ],
        [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            "☀️ Выберите прогноз погоды:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "☀️ Выберите прогноз погоды:",
            reply_markup=reply_markup
        )


async def handle_weather_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопок погоды"""
    query = update.callback_query
    data = query.data
    
    if data == "weather_today":
        await query.message.reply_text("⏳ Получаю данные о погоде...")
        weather_text = weather_service.get_current_weather()
        await query.message.reply_text(weather_text, parse_mode='HTML')
    
    elif data == "weather_week":
        await query.message.reply_text("⏳ Получаю прогноз на неделю...")
        forecast_text = weather_service.get_forecast(days=7)
        await query.message.reply_text(forecast_text, parse_mode='HTML')
