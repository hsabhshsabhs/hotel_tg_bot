"""
Обработчик модуля "Вопросы"
"""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from datetime import datetime

from services.google_sheets import GoogleSheetsService
from utils.state_manager import state_manager
from utils.auth import auth_service
from utils.validators import is_valid_date
from utils.formatters import format_date
from config import SHEET_NAMES
from logger import logger

sheets_service = GoogleSheetsService()


async def start_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать работу с модулем вопросов (как в GAS)"""
    chat_id = update.effective_chat.id
    
    state_manager.set_state(chat_id, {'mode': 'all_questions'})
    
    # Отправляем подменю как в GAS
    await send_questions_sub_menu(update, context)


async def send_questions_sub_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить подменю вопросов (как в GAS sendQuestionsSubMenu)"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить вопрос", callback_data="questions_add")],
        [InlineKeyboardButton("📋 Вопросы в работе", callback_data="questions_list")],
        [InlineKeyboardButton("🏗 Вопросы к комплексу", callback_data="main_complex")],
        [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            "Вопросы к заказчику:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Вопросы к заказчику:",
            reply_markup=reply_markup
        )


async def send_questions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить подменю вопросов к заказчику"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить вопрос", callback_data="questions_add")],
        [InlineKeyboardButton("📋 Вопросы в работе", callback_data="questions_list")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            "Вопросы к заказчику:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Вопросы к заказчику:",
            reply_markup=reply_markup
        )


async def send_complex_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить меню вопросов к комплексу (как в GAS)"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить вопрос", callback_data="complex_add")],
        [InlineKeyboardButton("📋 Список вопросов", callback_data="complex_list")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_all_questions")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            "Вопросы к комплексу:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Вопросы к комплексу:",
            reply_markup=reply_markup
        )


async def send_complex_protocol_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить меню протокола комплекса"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить вопрос", callback_data="protocol_add")],
        [InlineKeyboardButton("📋 Список вопросов", callback_data="protocol_list")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            "Протокол комплекса строительства:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Протокол комплекса строительства:",
            reply_markup=reply_markup
        )


async def handle_questions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопок вопросов (как в GAS)"""
    query = update.callback_query
    chat_id = query.from_user.id
    data = query.data
    state = state_manager.get_state(chat_id)
    
    # Вопросы к заказчику
    if data == "questions_add":
        state_manager.update_state(chat_id, step="awaiting_question_text")
        await query.message.reply_text("Введите наименование (текст) вопроса:")
    
    elif data == "questions_list":
        await send_in_progress_questions(update, context)
    
    # Вопросы к комплексу
    elif data == "main_complex":
        state_manager.update_state(chat_id, mode='complex')
        await send_complex_menu(update, context)
    
    elif data == "complex_add":
        state_manager.update_state(chat_id, step="awaiting_complex_text")
        await query.message.reply_text("Введите текст вопроса:")
    
    elif data == "complex_list":
        await send_executor_selection_menu(update, context)
    
    elif data.startswith("complex_show_"):
        executor = data.split("complex_show_")[1]
        await send_in_progress_complex_questions(update, context, executor)
    
    # Протокол комплекса
    elif data == "protocol_add":
        state_manager.update_state(chat_id, step="awaiting_protocol_text")
        await query.message.reply_text("Введите текст вопроса:")
    
    elif data == "protocol_list":
        await send_protocol_questions_list(update, context)
    
    elif data.startswith("protocol_"):
        await handle_protocol_callback(update, context, data)
    
    # Навигация
    elif data == "main_all_questions":
        await send_questions_sub_menu(update, context)
    
    elif data == "back_main":
        from handlers.main_menu import send_main_menu
        await send_main_menu(update, context)


async def handle_protocol_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Обработчик callback кнопок протокола комплекса"""
    query = update.callback_query
    chat_id = query.from_user.id
    parts = data.split("_")
    
    if len(parts) < 2:
        return
    
    action = parts[1]
    
    if action == "details":
        if len(parts) > 2:
            row_num = parts[2]
            await show_protocol_question_details(update, context, row_num)
    
    elif action == "complete":
        if len(parts) > 2:
            row_num = parts[2]
            await mark_protocol_question_complete(update, context, row_num)


async def send_protocol_questions_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить список вопросов протокола"""
    await send_all_protocol_questions(update, context)


async def send_in_progress_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить список вопросов в работе (как в GAS)"""
    try:
        questions_data = sheets_service.get_values(SHEET_NAMES['QUESTIONS'])
        
        if not questions_data or len(questions_data) < 10:
            await update.callback_query.message.reply_text("Вопросов со статусом 'В работе' не найдено.")
            await send_questions_sub_menu(update, context)
            return
        
        # Получаем данные из диапазона D10:G как в GAS
        in_progress_questions = []
        for row in questions_data[9:]:  # Начинаем с 10-й строки
            if len(row) > 3 and row[3] == "В работе" and row[0]:  # Колонка D (статус) и A (вопрос)
                in_progress_questions.append(row[0])
        
        if not in_progress_questions:
            message = "Вопросов со статусом 'В работе' не найдено."
        else:
            message = "<b>📋 Список вопросов в работе:</b>\n\n"
            for i, question in enumerate(in_progress_questions, 1):
                message += f"{i}. {question}\n\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="main_all_questions")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in send_in_progress_questions: {e}")
        await update.callback_query.message.reply_text("❌ Произошла ошибка при получении списка вопросов.")


async def add_question_to_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE, question_text: str):
    """Добавить вопрос в таблицу (как в GAS)"""
    try:
        # Получаем данные из листа "Вопросы к заказчику"
        questions_data = sheets_service.get_values(SHEET_NAMES['QUESTIONS'])
        
        # Ищем первую пустую строку начиная с 10-й (как в GAS)
        target_row = 10  # Начинаем с 10-й строки
        
        if questions_data:
            for i in range(9, len(questions_data)):  # Начинаем с 10-й строки (индекс 9)
                if len(questions_data[i]) > 3 and not questions_data[i][3]:  # Проверяем колонку D (статус)
                    target_row = i + 1  # +1 т.к. в Google Sheets нумерация с 1
                    break
        
        # Получаем имя инженера
        engineer_name = auth_service.get_engineer_name(update.effective_chat.id) or "Неизвестный"
        
        # Формируем дату как в GAS (dd.MM.yy)
        formatted_date = datetime.now().strftime('%d.%m.%y')
        
        # Записываем данные как в GAS:
        # Колонка C (3): Дата
        # Колонка D (4): Вопрос  
        # Колонка F (6): Инициатор
        sheets_service.update_cell(SHEET_NAMES['QUESTIONS'], f"C{target_row}", formatted_date)
        sheets_service.update_cell(SHEET_NAMES['QUESTIONS'], f"D{target_row}", question_text)
        sheets_service.update_cell(SHEET_NAMES['QUESTIONS'], f"F{target_row}", engineer_name)
        
        await update.message.reply_text(f"✅ Вопрос успешно добавлен в строку №{target_row}.")
        
        state_manager.delete_state(update.effective_chat.id)
        await send_questions_sub_menu(update, context)
        
    except Exception as e:
        logger.error(f"Error in add_question_to_sheet: {e}")
        await update.message.reply_text("❌ Произошла системная ошибка при записи вопроса.")


async def send_executor_selection_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить меню выбора исполнителя (как в GAS)"""
    try:
        protocol_data = sheets_service.get_values(SHEET_NAMES['COMPLEX_PROTOCOL'])
        
        if not protocol_data or len(protocol_data) < 4:
            await update.callback_query.message.reply_text(
                "Активных вопросов по исполнителям не найдено.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Назад", callback_data="main_complex")
                ]])
            )
            return
        
        # Собираем исполнителей как в GAS
        questions_by_executor = {}
        for row in protocol_data[3:]:  # Начинаем с 4-й строки
            if len(row) > 1 and str(row[1]).strip() == "В работе" and row[6]:  # Статус и исполнитель
                executor = row[6]
                if executor not in questions_by_executor:
                    questions_by_executor[executor] = 0
                questions_by_executor[executor] += 1
        
        if not questions_by_executor:
            await update.callback_query.message.reply_text(
                "Активных вопросов по исполнителям не найдено.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Назад", callback_data="main_complex")
                ]])
            )
            return
        
        keyboard = []
        for executor, count in questions_by_executor.items():
            keyboard.append([InlineKeyboardButton(
                f"{executor} - {count}",
                callback_data=f"complex_show_{executor}"
            )])
        
        keyboard.append([InlineKeyboardButton("📋 Показать все вопросы", callback_data="complex_show_all")])
        keyboard.append([InlineKeyboardButton("⬅️ Назад в меню комплекса", callback_data="main_complex")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text(
            "Выберите исполнителя для просмотра вопросов:",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in send_executor_selection_menu: {e}")
        await update.callback_query.message.reply_text("❌ Ошибка при формировании списка исполнителей.")


async def send_in_progress_complex_questions(update: Update, context: ContextTypes.DEFAULT_TYPE, executor_filter: str = None):
    """Отправить вопросы к комплексу в работе (как в GAS)"""
    try:
        protocol_data = sheets_service.get_values(SHEET_NAMES['COMPLEX_PROTOCOL'])
        
        if not protocol_data or len(protocol_data) < 4:
            await update.callback_query.message.reply_text("Вопросов со статусом 'В работе' не найдено.")
            await send_complex_menu(update, context)
            return
        
        # Получаем данные из диапазона A4:G как в GAS
        in_progress_questions = []
        for i, row in enumerate(protocol_data[3:], start=4):  # Начинаем с 4-й строки
            if len(row) > 1 and str(row[1]).strip() == "В работе" and row[0]:  # Статус и вопрос
                question_data = {
                    'text': row[0],
                    'deadline': row[2] if len(row) > 2 else '',
                    'assignee': row[6] if len(row) > 6 else ''
                }
                
                if executor_filter and executor_filter != 'all' and question_data['assignee'] != executor_filter:
                    continue
                
                in_progress_questions.append(question_data)
        
        if not in_progress_questions:
            filter_text = f" для исполнителя {executor_filter}" if executor_filter and executor_filter != 'all' else ''
            message = f"Вопросов со статусом 'В работе'{filter_text} не найдено."
        else:
            title = f"по исполнителю {executor_filter}" if executor_filter and executor_filter != 'all' else 'все'
            message = f"<b>📋 Список вопросов комплекса в работе ({title}):</b>\n\n"
            
            for i, q in enumerate(in_progress_questions, 1):
                deadline = q['deadline'] if q['deadline'] else "не указан"
                message += f"<b>{i}. Вопрос:</b> {q['text']}\n"
                message += f"<b>Срок:</b> {deadline}\n"
                message += f"<b>Исполнитель:</b> {q['assignee']}\n\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад к выбору исполнителя", callback_data="complex_list")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in send_in_progress_complex_questions: {e}")
        await update.callback_query.message.reply_text("❌ Ошибка при получении списка вопросов.")


async def send_all_protocol_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить все вопросы протокола комплекса"""
    try:
        protocol_data = sheets_service.get_values(SHEET_NAMES['COMPLEX_PROTOCOL'])
        
        if not protocol_data or len(protocol_data) < 4:
            await update.callback_query.message.reply_text("Активных вопросов к комплексу нет.")
            return
        
        active_questions = []
        for i, row in enumerate(protocol_data[3:], start=4):  # Начинаем с 4-й строки
            if len(row) > 1 and str(row[1]).strip() == "В работе" and row[0]:
                active_questions.append({
                    'data': row,
                    'row_num': i
                })
        
        if not active_questions:
            await update.callback_query.message.reply_text("Активных вопросов к комплексу нет.")
            return
        
        keyboard = []
        for q in active_questions:
            initiator = q['data'][7] if len(q['data']) > 7 else ''
            question_text = (q['data'][0][:25] + "...") if len(q['data'][0]) > 25 else q['data'][0]
            keyboard.append([InlineKeyboardButton(
                f"От {initiator}: {question_text}",
                callback_data=f"protocol_details_{q['row_num']}"
            )])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="protocol_add")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text(
            "Выберите вопрос для просмотра или изменения статуса:",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in send_all_protocol_questions: {e}")
        await update.callback_query.message.reply_text("❌ Ошибка при получении вопросов.")


async def show_protocol_question_details(update: Update, context: ContextTypes.DEFAULT_TYPE, row_num: str):
    """Показать детали вопроса протокола"""
    try:
        protocol_data = sheets_service.get_values(SHEET_NAMES['COMPLEX_PROTOCOL'])
        row_index = int(row_num)
        
        if row_index >= len(protocol_data):
            await update.callback_query.message.reply_text("Ошибка: Вопрос не найден.")
            return
        
        row_data = protocol_data[row_index]
        
        # Получаем номер вопроса из колонки A
        question_number = sheets_service.get_values(SHEET_NAMES['COMPLEX_PROTOCOL'], f"A{row_index}:A{row_index}")
        question_num = question_number[0][0] if question_number else row_index
        
        # Формируем сообщение
        message = f"<b>Вопрос №{question_num}</b>\n\n"
        message += f"<b>Текст:</b> {row_data[0]}\n"
        message += f"<b>Статус:</b> {row_data[1]}\n"
        message += f"<b>Срок решения:</b> {row_data[2] if len(row_data) > 2 else ''}\n"
        message += f"<b>Дата возникновения:</b> {row_data[7] if len(row_data) > 7 else ''}\n"
        message += f"<b>Инициатор:</b> {row_data[9] if len(row_data) > 9 else ''}"
        
        keyboard = [[
            InlineKeyboardButton("✅ Отметить выполненным", callback_data=f"protocol_complete_{row_num}")
        ], [
            InlineKeyboardButton("⬅️ К списку вопросов", callback_data="protocol_list")
        ]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in show_protocol_question_details: {e}")
        await update.callback_query.message.reply_text("❌ Ошибка при получении деталей вопроса.")


async def mark_protocol_question_complete(update: Update, context: ContextTypes.DEFAULT_TYPE, row_num: str):
    """Отметить вопрос протокола как выполненный"""
    try:
        row_index = int(row_num)
        
        # Получаем номер вопроса для сообщения
        question_number = sheets_service.get_values(SHEET_NAMES['COMPLEX_PROTOCOL'], f"A{row_index}:A{row_index}")
        question_num = question_number[0][0] if question_number else row_index
        
        # Обновляем статус на "Выполнено"
        sheets_service.update_cell(SHEET_NAMES['COMPLEX_PROTOCOL'], f"B{row_index}", "Выполнено")
        
        await update.callback_query.message.reply_text(f"✅ Статус вопроса №{question_num} изменен на 'Выполнено'.")
        await send_all_protocol_questions(update, context)
        
    except Exception as e:
        logger.error(f"Error in mark_protocol_question_complete: {e}")
        await update.callback_query.message.reply_text("❌ Ошибка при обновлении статуса вопроса.")


async def handle_questions_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений в модуле вопросов"""
    chat_id = update.effective_chat.id
    text = update.message.text
    state = state_manager.get_state(chat_id)
    
    if not state:
        return
    
    step = state.get('step')
    
    # Вопросы к заказчику
    if step == "awaiting_question_text":
        await add_question_to_sheet(update, context, text)
    
    # Вопросы к комплексу
    elif step == "awaiting_complex_text":
        state_manager.update_state(chat_id, complexText=text, step="awaiting_complex_deadline")
        await update.message.reply_text("✅ Текст принят. Теперь введите срок выполнения (например, 01.12.2025):")
    
    elif step == "awaiting_complex_deadline":
        if is_valid_date(text):
            state_manager.update_state(chat_id, complexDeadline=text, step="awaiting_complex_assignee")
            await update.message.reply_text("✅ Срок принят. Теперь укажите исполнителя (кому адресован вопрос):")
        else:
            await update.message.reply_text("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
    
    elif step == "awaiting_complex_assignee":
        state_manager.update_state(chat_id, complexAssignee=text)
        await add_complex_question_to_sheet(update, context, state)
    
    # Протокол комплекса
    elif step == "awaiting_protocol_text":
        state_manager.update_state(chat_id, protocolText=text, step="awaiting_protocol_deadline")
        await update.message.reply_text("✅ Текст принят. Теперь введите срок выполнения (например, 01.12.2025):")
    
    elif step == "awaiting_protocol_deadline":
        if is_valid_date(text):
            state_manager.update_state(chat_id, protocolDeadline=text, step="awaiting_protocol_assignee")
            await update.message.reply_text("✅ Срок принят. Теперь укажите исполнителя (кому адресован вопрос):")
        else:
            await update.message.reply_text("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
    
    elif step == "awaiting_protocol_assignee":
        state_manager.update_state(chat_id, protocolAssignee=text)
        await add_protocol_question_to_sheet(update, context, state)


async def add_complex_question_to_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
    """Добавить вопрос к комплексу в таблицу (как в GAS)"""
    try:
        # Получаем данные из листа "Протокол комплекса строительства"
        protocol_data = sheets_service.get_values(SHEET_NAMES['COMPLEX_PROTOCOL'])
        
        # Ищем первую пустую строку начиная с 4-й (как в GAS)
        target_row = 4
        
        if protocol_data:
            for i in range(3, len(protocol_data)):  # Начинаем с 4-й строки (индекс 3)
                if len(protocol_data[i]) > 0 and not protocol_data[i][0]:  # Проверяем колонку A (вопрос)
                    target_row = i + 1  # +1 т.к. в Google Sheets нумерация с 1
                    break
        
        # Получаем имя инженера
        engineer_name = auth_service.get_engineer_name(update.effective_chat.id) or "Неизвестный"
        
        # Записываем данные как в GAS:
        # Колонка A (1): Вопрос
        # Колонка B (2): Статус "В работе"
        # Колонка C (3): Срок
        # Колонка G (7): Исполнитель
        # Колонка H (8): Дата
        # Колонка J (10): Инициатор
        sheets_service.update_cell(SHEET_NAMES['COMPLEX_PROTOCOL'], f"A{target_row}", state.get('complexText'))
        sheets_service.update_cell(SHEET_NAMES['COMPLEX_PROTOCOL'], f"B{target_row}", "В работе")
        sheets_service.update_cell(SHEET_NAMES['COMPLEX_PROTOCOL'], f"C{target_row}", state.get('complexDeadline'))
        sheets_service.update_cell(SHEET_NAMES['COMPLEX_PROTOCOL'], f"G{target_row}", state.get('complexAssignee'))
        sheets_service.update_cell(SHEET_NAMES['COMPLEX_PROTOCOL'], f"H{target_row}", datetime.now().strftime('%d.%m.%Y'))
        sheets_service.update_cell(SHEET_NAMES['COMPLEX_PROTOCOL'], f"J{target_row}", engineer_name)
        
        await update.message.reply_text(f"✅ Вопрос для комплекса успешно добавлен в строку №{target_row}.")
        
        state_manager.delete_state(update.effective_chat.id)
        await send_complex_menu(update, context)
        
    except Exception as e:
        logger.error(f"Error in add_complex_question_to_sheet: {e}")
        await update.message.reply_text("❌ Произошла системная ошибка при записи вопроса.")


async def add_protocol_question_to_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
    """Добавить вопрос протокола комплекса в таблицу"""
    try:
        # Получаем данные из листа "Вопросы к комплексу"
        complex_questions_data = sheets_service.get_values(SHEET_NAMES['COMPLEX_QUESTIONS'])
        
        # Ищем последнюю строку
        target_row = len(complex_questions_data) + 1 if complex_questions_data else 2
        
        # Получаем имя инженера
        engineer_name = auth_service.get_engineer_name(update.effective_chat.id) or "Неизвестный"
        
        # Формируем данные для новой строки
        new_row_data = [
            "",  # Номер (будет заполнено автоматически)
            state.get('protocolText'),  # Вопрос
            "В работе",  # Статус
            "",  # Срок
            "",  # 
            "",  # 
            datetime.now().strftime('%d.%m.%Y'),  # Дата
            engineer_name,  # Инициатор
        ]
        
        # Добавляем строку в таблицу
        sheets_service.append_row(SHEET_NAMES['COMPLEX_QUESTIONS'], new_row_data)
        
        # Обновляем номер вопроса
        if target_row > 2:
            last_question_number = sheets_service.get_values(SHEET_NAMES['COMPLEX_QUESTIONS'], f"A{target_row-1}:A{target_row-1}")
            last_num = last_question_number[0][0] if last_question_number and last_question_number[0][0] else 0
            new_question_number = (int(last_num) if isinstance(last_num, (int, float)) else 0) + 1
        else:
            new_question_number = 1
        
        sheets_service.update_cell(SHEET_NAMES['COMPLEX_QUESTIONS'], f"A{target_row}", new_question_number)
        
        await update.message.reply_text(f"✅ Ваш вопрос №{new_question_number} успешно зарегистрирован.")
        
        state_manager.delete_state(update.effective_chat.id)
        await send_complex_protocol_menu(update, context)
        
    except Exception as e:
        logger.error(f"Error in add_protocol_question_to_sheet: {e}")
        await update.message.reply_text("❌ Произошла системная ошибка при добавлении вопроса.")
