"""
Обработчик модуля "Журнал ПСД" (распознавание документов)
"""
from telegram import Update
from telegram.ext import ContextTypes

from services.google_drive import GoogleDriveService
from services.gemini_vision import GeminiVisionService
from utils.state_manager import state_manager
from logger import logger

drive_service = GoogleDriveService()
gemini_service = GeminiVisionService()


async def start_psd_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать работу с модулем ПСД"""
    chat_id = update.effective_chat.id
    
    state_manager.set_state(chat_id, {
        'mode': 'psd_log',
        'step': 'awaiting_invoice_photo'
    })
    
    await update.message.reply_text(
        "📄 Отправьте фотографию накладной для добавления проектов в журнал."
    )


async def handle_psd_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фото накладной"""
    chat_id = update.effective_chat.id
    state = state_manager.get_state(chat_id)
    
    if state.get('step') != 'awaiting_invoice_photo':
        await update.message.reply_text(
            "Я не ожидал получить фото. Используйте кнопки меню."
        )
        return
    
    await update.message.reply_text(
        "⏳ Получил накладную. Отправляю на распознавание, это может занять до минуты..."
    )
    
    try:
        # Получаем фото
        photo = update.message.photo[-1]  # Берем самое большое фото
        file = await context.bot.get_file(photo.file_id)
        
        # Скачиваем фото
        photo_bytes = await file.download_as_bytearray()
        
        # Загружаем в Google Drive
        filename = f"invoice_{chat_id}_{photo.file_id}.jpg"
        photo_url = drive_service.upload_photo(bytes(photo_bytes), filename)
        
        if not photo_url:
            await update.message.reply_text(
                "❌ Ошибка загрузки фото в Google Drive. Попробуйте еще раз."
            )
            return
        
        # Распознаем через Gemini Vision
        invoice_data = gemini_service.recognize_invoice(bytes(photo_bytes))
        
        if 'error' in invoice_data:
            await update.message.reply_text(
                f"❌ Ошибка распознавания: {invoice_data['error']}\n\n"
                f"Попробуйте сделать более четкое фото."
            )
            state_manager.delete_state(chat_id)
            return
        
        # TODO: Проверить дубликаты и добавить в журнал
        
        await update.message.reply_text(
            f"✅ Накладная распознана!\n\n"
            f"📋 Номер: {invoice_data.get('number', 'б/н')}\n"
            f"📅 Дата: {invoice_data.get('date', '-')}\n"
            f"🏢 Объект: {invoice_data.get('objectName', '-')}\n"
            f"👷 Подрядчик: {invoice_data.get('contractor', '-')}\n"
            f"📦 Проектов: {len(invoice_data.get('items', []))}\n\n"
            f"Функция добавления в журнал в разработке."
        )
        
        state_manager.delete_state(chat_id)
    
    except Exception as e:
        logger.error(f"Error processing invoice photo: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке накладной. Попробуйте еще раз."
        )
        state_manager.delete_state(chat_id)


async def handle_psd_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текста в режиме ПСД"""
    await update.message.reply_text(
        "❌ Пожалуйста, отправьте фото накладной, а не текст."
    )
