"""
Обработчик модуля "Недельно-суточное задание" (НСЗ)
"""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from utils.state_manager import state_manager
from utils.auth import auth_service
from logger import logger


async def start_nsg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать работу с модулем НСЗ"""
    chat_id = update.effective_chat.id
    user_role = auth_service.get_user_role(chat_id)
    
    state_manager.set_state(chat_id, {'mode': 'nsg'})
    
    await send_nsg_menu(update, context, user_role)


async def send_nsg_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user_role: str = None):
    """Отправить меню НСЗ"""
    if user_role is None:
        user_role = auth_service.get_user_role(update.effective_chat.id)
    
    message = "Раздел: Недельно-суточное задание\n\n"
    
    if user_role == "ИНЖЕНЕР":
        message += "Выберите действие:"
        keyboard = [
            [InlineKeyboardButton("📊 Сводная таблица", callback_data="nsg_dashboard")],
            [InlineKeyboardButton("📋 План на утверждении", callback_data="nsg_pending")],
            [InlineKeyboardButton("📁 Архив планов", callback_data="nsg_archive")],
            [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_main")]
        ]
    else:
        message += "Выберите период для заполнения НСЗ или откройте сводную таблицу:"
        keyboard = [
            [InlineKeyboardButton("📅 Текущая неделя", callback_data="nsg_current_week")],
            [InlineKeyboardButton("📅 Следующая неделя", callback_data="nsg_next_week")],
            [InlineKeyboardButton("📊 Сводная таблица", callback_data="nsg_dashboard")],
            [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_main")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)


async def handle_nsg_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопок НСЗ"""
    query = update.callback_query
    chat_id = query.from_user.id
    data = query.data
    user_role = auth_service.get_user_role(chat_id)
    
    if data == "nsg_current_week":
        await query.message.reply_text(
            "📅 Форма для текущей недели\n\n"
            "🔧 В разработке: интеграция с Google Forms для заполнения НСЗ\n\n"
            "Временно используйте веб-версию для заполнения планов."
        )
    
    elif data == "nsg_next_week":
        await query.message.reply_text(
            "📅 Форма для следующей недели\n\n"
            "🔧 В разработке: интеграция с Google Forms для заполнения НСЗ\n\n"
            "Временно используйте веб-версию для заполнения планов."
        )
    
    elif data == "nsg_dashboard":
        await query.message.reply_text(
            "📊 Сводная таблица НСЗ\n\n"
            "🔧 В разработке: панель управления с графиками и статистикой\n\n"
            "Временно используйте Google Sheets для просмотра данных."
        )
    
    elif data == "nsg_pending" and user_role == "ИНЖЕНЕР":
        await query.message.reply_text(
            "📋 Планы на утверждении\n\n"
            "🔧 В разработке: список планов ожидающих утверждения\n\n"
            "Временно проверьте лист 'НСЗ' в Google Sheets."
        )
    
    elif data == "nsg_archive" and user_role == "ИНЖЕНЕР":
        await query.message.reply_text(
            "📁 Архив планов НСЗ\n\n"
            "🔧 В разработке: просмотр архивных данных\n\n"
            "Временно проверьте лист 'Архив НСЗ' в Google Sheets."
        )


async def handle_nsg_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений в режиме НСЗ"""
    await update.message.reply_text(
        "📋 Используйте кнопки меню для работы с НСЗ\n\n"
        "Для заполнения планов воспользуйтесь веб-формой или свяжитесь с инженером."
    )
