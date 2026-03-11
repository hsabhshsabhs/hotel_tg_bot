"""
Главный файл Telegram бота для управления строительством отеля
"""
import asyncio
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from config import TELEGRAM_BOT_TOKEN, validate_config
from logger import logger, log_to_sheet
from utils.state_manager import state_manager
from utils.auth import auth_service

# Импорт обработчиков (будут созданы далее)
from handlers import main_menu, headcount, tasks, questions, weather, psd_log, nsg


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    logger.info(f"User {chat_id} ({user.username}) started the bot")
    log_to_sheet("INFO", f"User {chat_id} started bot")
    
    # Очищаем состояние пользователя
    state_manager.delete_state(chat_id)
    
    # Отправляем главное меню
    await main_menu.send_main_menu(update, context)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    chat_id = update.effective_chat.id
    text = update.message.text
    
    logger.debug(f"Text message from {chat_id}: {text}")
    
    # Получаем текущее состояние пользователя
    state = state_manager.get_state(chat_id)
    mode = state.get('mode')
    
    # Обработка кнопок главного меню
    if text == 'АО "Прокатмонтаж" Гостиница':
        await main_menu.send_main_menu(update, context)
        return
    
    if text == "⠀":  # Пустая кнопка
        return
    
    # Маршрутизация по основным кнопкам
    if text == "👷 Численность":
        await headcount.start_headcount(update, context)
        return
    
    if text == "🎯 Целевые задания":
        await tasks.start_tasks(update, context)
        return
    
    if text == "🗓️ Недельно-суточное задание":
        await nsg.start_nsg(update, context)
        return
    
    if text == "❓ Вопросы":
        await questions.start_questions(update, context)
        return
    
    if text == "☀️ Погода":
        await weather.show_weather_menu(update, context)
        return
    
    if text == "📄 Добавить ПСД":
        if auth_service.is_engineer(chat_id):
            await psd_log.start_psd_log(update, context)
        else:
            await update.message.reply_text("❌ У вас нет доступа к этому разделу.")
        return
    
    # Если пользователь в процессе заполнения - передаем в соответствующий обработчик
    if mode == 'headcount':
        await headcount.handle_headcount_text(update, context)
    elif mode == 'tasks':
        await tasks.handle_tasks_text(update, context)
    elif mode == 'questions':
        await questions.handle_questions_text(update, context)
    elif mode == 'psd_log':
        await psd_log.handle_psd_text(update, context)
    else:
        # Неизвестная команда
        await update.message.reply_text(
            "Я не понял вашу команду. Используйте кнопки меню или /start"
        )


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фотографий"""
    chat_id = update.effective_chat.id
    
    logger.debug(f"Photo received from {chat_id}")
    
    state = state_manager.get_state(chat_id)
    mode = state.get('mode')
    
    if mode == 'tasks':
        await tasks.handle_tasks_photo(update, context)
    elif mode == 'psd_log':
        await psd_log.handle_psd_photo(update, context)
    else:
        await update.message.reply_text(
            "Я не ожидал получить фото. Чтобы начать, нажмите /start"
        )


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик inline кнопок"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.from_user.id
    data = query.data
    
    logger.debug(f"Callback from {chat_id}: {data}")
    
    state = state_manager.get_state(chat_id)
    mode = state.get('mode')
    
    # Обработка кнопки "Назад в главное меню"
    if data == 'back_main':
        state_manager.delete_state(chat_id)
        await main_menu.send_main_menu(update, context)
        return
    
    # Маршрутизация по модулям
    if data.startswith('main_'):
        # Переход в основной модуль
        module = data.split('_')[1]
        
        if module == 'headcount':
            await headcount.start_headcount(update, context)
        elif module == 'tasks':
            await tasks.start_tasks(update, context)
        elif module == 'questions':
            await questions.start_questions(update, context)
        elif module == 'weather':
            await weather.show_weather_menu(update, context)
        elif module == 'nsg':
            await nsg.start_nsg(update, context)
        elif module == 'complex':
            await questions.handle_complex_callback(update, context, data)
        elif module == 'all_questions':
            await questions.send_questions_sub_menu(update, context)
    
    # Передаем в обработчики модулей
    elif mode == 'headcount' or data.startswith(('headcount_', 'date_', 'org_', 'dir_', 'shift_')):
        await headcount.handle_headcount_callback(update, context)
    elif mode == 'tasks' or data.startswith(('task_', 'engineer_', 'contractor_', 'back_')):
        await tasks.handle_tasks_callback(update, context)
    elif mode == 'questions' or data.startswith(('questions_', 'complex_', 'protocol_', 'main_')):
        await questions.handle_questions_callback(update, context)
    elif mode == 'weather' or data.startswith('weather_'):
        await weather.handle_weather_callback(update, context)
    elif mode == 'nsg' or data.startswith('nsg_'):
        await nsg.handle_nsg_callback(update, context)
    elif mode == 'psd_log' or data.startswith('psd_'):
        await psd_log.handle_psd_log_callback(update, context)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error: {context.error}")
    
    # Если ошибка связана с вебхуком, пытаемся его удалить
    if "webhook" in str(context.error).lower():
        logger.info("🔄 Попытка удалить вебхук из-за ошибки...")
        await delete_webhook()


async def delete_webhook():
    """Удалить вебхук при запуске бота"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
        response = requests.get(url, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            logger.info("✅ Вебхук успешно удален")
        else:
            logger.warning(f"⚠️ Предупреждение при удалении вебхука: {result}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении вебхука: {e}")


def main():
    """Главная функция запуска бота"""
    try:
        # Валидация конфигурации
        logger.info("Проверка конфигурации...")
        validate_config()
        
        logger.info("🚀 Запуск бота...")
        
        # Удаляем вебхук через синхронный запрос
        logger.info("🔄 Проверка и удаление вебхука...")
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
            response = requests.get(url, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                logger.info("✅ Вебхук успешно удален")
            else:
                logger.warning(f"⚠️ Предупреждение при удалении вебхука: {result}")
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении вебхука: {e}")
        
        # Создание приложения
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Регистрация обработчиков команд
        application.add_handler(CommandHandler("start", start_command))
        
        # Регистрация обработчиков сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
        
        # Регистрация обработчика inline кнопок
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Регистрация обработчика ошибок
        application.add_error_handler(error_handler)
        
        logger.info("✅ Бот успешно запущен и готов к работе!")
        logger.info("Нажмите Ctrl+C для остановки")
        
        # Запуск бота
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        raise


if __name__ == '__main__':
    main()
