"""
Обработчик главного меню
"""
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from utils.auth import auth_service
from utils.state_manager import state_manager
from logger import logger


async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отправить главное меню пользователю
    
    Args:
        update: Update объект Telegram
        context: Context объект
    """
    chat_id = update.effective_chat.id
    user_role = auth_service.get_user_role(chat_id)
    
    # Очищаем состояние
    state_manager.delete_state(chat_id)
    
    # Формируем клавиатуру
    keyboard = [
        [
            KeyboardButton("👷 Численность"),
            KeyboardButton("🎯 Целевые задания")
        ],
        [
            KeyboardButton("🗓️ Недельно-суточное задание"),
            KeyboardButton("❓ Вопросы")
        ]
    ]
    
    # Третья строка зависит от роли
    third_row = [KeyboardButton("☀️ Погода")]
    
    if user_role == "ИНЖЕНЕР":
        third_row.append(KeyboardButton("📄 Добавить ПСД"))
    else:
        third_row.append(KeyboardButton("⠀"))  # Пустая кнопка для симметрии
    
    keyboard.append(third_row)
    
    # Четвертая строка - название компании
    keyboard.append([KeyboardButton('АО "Прокатмонтаж" Гостиница')])
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True
    )
    
    welcome_text = "Добро пожаловать! Выберите раздел:"
    
    # Отправляем сообщение
    if update.callback_query:
        await update.callback_query.message.reply_text(
            welcome_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup
        )
    
    logger.info(f"Main menu sent to {chat_id} (role: {user_role})")
