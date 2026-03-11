"""
Обработчик модуля "Целевые задания"  
"""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from datetime import datetime

from services.google_sheets import GoogleSheetsService
from utils.state_manager import state_manager
from utils.auth import auth_service
from utils.validators import is_valid_date
from utils.formatters import format_date, truncate_text
from config import SHEET_NAMES
from logger import logger

sheets_service = GoogleSheetsService()


async def start_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать работу с модулем заданий"""
    chat_id = update.effective_chat.id
    user_role = auth_service.get_user_role(chat_id)
    
    state_manager.set_state(chat_id, {'mode': 'tasks'})
    
    if user_role == "ИНЖЕНЕР":
        await send_engineer_task_menu(update, context)
    else:
        # Подрядчику показываем список организаций
        await send_contractor_org_list(update, context, "Выберите вашу организацию:")


async def send_engineer_task_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить меню инженера"""
    keyboard = [
        [InlineKeyboardButton("➕ Создать задание", callback_data="engineer_create")],
        [InlineKeyboardButton("🔎 Задания на проверке", callback_data="engineer_review")],
        [InlineKeyboardButton("📋 По подрядчикам", callback_data="engineer_by_contractor")],
        [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            "Раздел: Целевые задания",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Раздел: Целевые задания",
            reply_markup=reply_markup
        )


async def send_contractor_org_list(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    """Отправить список организаций подрядчикам"""
    contractors = auth_service.get_contractors_list()
    
    keyboard = []
    for contractor in contractors:
        keyboard.append([InlineKeyboardButton(contractor, callback_data=f"contractor_{contractor}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Главное меню", callback_data="back_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)


async def handle_tasks_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопок заданий"""
    query = update.callback_query
    chat_id = query.from_user.id
    data = query.data
    user_role = auth_service.get_user_role(chat_id)
    state = state_manager.get_state(chat_id)
    
    # Кнопки "Назад"
    if data == "back_engineer_menu":
        state_manager.delete_state(chat_id)
        await send_engineer_task_menu(update, context)
        return
    elif data == "back_contractor_list":
        await send_contractor_org_list(update, context, "Выберите подрядчика для просмотра заданий:")
        return
    
    if user_role == "ИНЖЕНЕР":
        if data == "engineer_create":
            state_manager.update_state(chat_id, step="awaiting_contractor_choice")
            await send_contractor_org_list(update, context, "Выберите подрядчика для нового задания:")
        
        elif data == "engineer_review":
            await send_tasks_for_review(update, context)
        
        elif data == "engineer_by_contractor":
            await send_contractor_org_list(update, context, "Выберите подрядчика для просмотра заданий:")
        
        elif data.startswith("contractor_"):
            contractor_name = data.split("_", 1)[1]
            if state.get('step') == "awaiting_contractor_choice":
                state_manager.update_state(chat_id, contractor=contractor_name, step="awaiting_task_text")
                await query.message.reply_text(f'Подрядчик "{contractor_name}" выбран.\n\nВведите текст задания:')
            else:
                await show_tasks_to_contractor(update, context, contractor_name)
        
        elif data.startswith("task_"):
            await handle_engineer_task_callback(update, context, data)
    
    else:  # ПОДРЯДЧИК
        if data.startswith("contractor_"):
            contractor_name = data.split("_", 1)[1]
            await show_tasks_to_contractor(update, context, contractor_name)
        
        elif data.startswith("task_"):
            await handle_contractor_task_callback(update, context, data)


async def handle_engineer_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Обработчик callback кнопок инженера для заданий"""
    query = update.callback_query
    chat_id = query.from_user.id
    state = state_manager.get_state(chat_id)
    parts = data.split("_")
    
    if len(parts) < 3:
        return
    
    task_action = parts[1]
    task_number = parts[2]
    
    if task_action != 'rate':
        state_manager.update_state(chat_id, taskNumber=task_number)
    
    if task_action == "accept":
        await ask_for_rating(update, context)
    elif task_action == "rework":
        state_manager.update_state(chat_id, step="awaiting_rework_comment")
        await query.message.reply_text("Введите комментарий для подрядчика (причину возврата):")
    elif task_action == "rate":
        rating = task_number
        await accept_task(update, context, state, rating)
    elif task_action == "delete":
        await delete_task_and_renumber(update, context, state.get('taskNumber'))
    elif task_action == "review":
        await show_task_to_engineer(update, context, task_number, "review")


async def handle_contractor_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Обработчик callback кнопок подрядчика для заданий"""
    query = update.callback_query
    chat_id = query.from_user.id
    state = state_manager.get_state(chat_id)
    parts = data.split("_")
    
    if len(parts) < 3:
        return
    
    task_action = parts[1]
    task_number = parts[2]
    
    if task_action == "show":
        contractor_name = state.get('contractor')
        await show_task_details_to_contractor(update, context, contractor_name, task_number)
    elif task_action == "execute":
        state_manager.update_state(chat_id, step="awaiting_report_text", taskNumber=task_number)
        await query.message.reply_text("Введите текст отчета о выполнении задания:")


async def send_tasks_for_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить задания на проверку"""
    try:
        tasks_data = sheets_service.get_values(SHEET_NAMES['TASKS'])
        tasks_to_review = []
        
        for row in tasks_data[1:]:  # Пропускаем заголовок
            if len(row) > 1 and row[1] == "На проверке":
                tasks_to_review.append(row)
        
        if not tasks_to_review:
            await update.callback_query.message.reply_text("Заданий, ожидающих проверки, нет.")
            return
        
        keyboard = []
        for task in tasks_to_review:
            task_text = truncate_text(task[3] if len(task) > 3 else "", 15)
            keyboard.append([InlineKeyboardButton(
                f"№{task[0]} ({task[2]}) - {task_text}...",
                callback_data=f'task_review_{task[0]}'
            )])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_engineer_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text("Выберите задание для проверки:", reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Error in send_tasks_for_review: {e}")
        await update.callback_query.message.reply_text("❌ Ошибка при получении заданий на проверку.")


async def show_tasks_to_contractor(update: Update, context: ContextTypes.DEFAULT_TYPE, contractor_name: str):
    """Показать задания подрядчику"""
    try:
        tasks_data = sheets_service.get_values(SHEET_NAMES['TASKS'])
        contractor_tasks = []
        
        for row in tasks_data[1:]:  # Пропускаем заголовок
            if (len(row) > 2 and 
                row[2] == contractor_name and 
                row[1] in ["Новое", "На доработке", "В работе"]):
                contractor_tasks.append(row)
        
        if not contractor_tasks:
            await update.callback_query.message.reply_text(
                "Для вашей организации нет активных заданий.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Назад к выбору", callback_data="back_contractor_list")
                ]])
            )
            return
        
        keyboard = []
        for task in contractor_tasks:
            task_text = truncate_text(task[3] if len(task) > 3 else "", 30)
            keyboard.append([InlineKeyboardButton(
                f"({task[1]}) {task_text}...",
                callback_data=f'task_show_{task[0]}'
            )])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад к выбору", callback_data="back_contractor_list")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text(
            f'Активные задания для "{contractor_name}":',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in show_tasks_to_contractor: {e}")
        await update.callback_query.message.reply_text("❌ Ошибка при получении заданий.")


async def show_task_details_to_contractor(update: Update, context: ContextTypes.DEFAULT_TYPE, contractor_name: str, task_number: str):
    """Показать детали задания подрядчику"""
    try:
        task_data = await get_task_by_number(task_number)
        
        if not task_data or task_data.get('Подрядчик') != contractor_name:
            await update.callback_query.message.reply_text("Ошибка: Задание не найдено.")
            return
        
        message = f"<b>Задание №{task_data.get('Номер')}</b>\n\n"
        message += f"<b>Текст:</b> {task_data.get('Текст задания', '')}\n"
        
        task_photo_link = task_data.get('Фото задания')
        if task_photo_link and task_photo_link.startswith("http"):
            message += f"<b>Фото к заданию:</b> <a href=\"{task_photo_link}\">Посмотреть</a>\n"
        
        message += f"<b>Срок выполнения:</b> {task_data.get('Срок выполнения', '')}\n"
        
        if task_data.get('Статус') == "На доработке" and task_data.get('Комментарий инженера'):
            message += f"\n❗️<b>Комментарий инженера:</b> <i>{task_data['Комментарий инженера']}</i>\n"
        
        keyboard = [[
            InlineKeyboardButton("📝 Выполнить задание", callback_data=f"task_execute_{task_number}")
        ], [
            InlineKeyboardButton("⬅️ К списку заданий", callback_data=f"contractor_{contractor_name}")
        ]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in show_task_details_to_contractor: {e}")
        await update.callback_query.message.reply_text("❌ Ошибка при получении деталей задания.")


async def ask_for_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запросить оценку выполненной работы"""
    keyboard = [[
        InlineKeyboardButton("⭐ 1", callback_data="task_rate_1"),
        InlineKeyboardButton("⭐ 2", callback_data="task_rate_2"),
        InlineKeyboardButton("⭐ 3", callback_data="task_rate_3"),
        InlineKeyboardButton("⭐ 4", callback_data="task_rate_4"),
        InlineKeyboardButton("⭐ 5", callback_data="task_rate_5")
    ]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Оцените выполненную работу:", reply_markup=reply_markup)


async def get_task_by_number(task_number: str) -> dict:
    """Получить задание по номеру"""
    try:
        tasks_data = sheets_service.get_values(SHEET_NAMES['TASKS'])
        
        for row in tasks_data[1:]:  # Пропускаем заголовок
            if len(row) > 0 and str(row[0]) == task_number:
                # Преобразуем в словарь для удобства
                headers = ["Номер", "Статус", "Подрядчик", "Текст задания", "Фото задания", "", "Срок выполнения", "", "", "", "Инициатор", "", "", "", "", ""]
                task_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        task_dict[header] = row[i]
                return task_dict
        
        return None
        
    except Exception as e:
        logger.error(f"Error in get_task_by_number: {e}")
        return None


async def handle_tasks_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений в режиме заданий"""
    chat_id = update.effective_chat.id
    text = update.message.text
    state = state_manager.get_state(chat_id)
    step = state.get('step')
    
    if step == "awaiting_task_text":
        state_manager.update_state(chat_id, taskText=text, step="awaiting_task_photo_needed")
        await ask_if_photo_needed(update, context)
    
    elif step == "awaiting_task_deadline":
        validation_result = is_valid_date(text)
        if validation_result:
            state_manager.update_state(chat_id, deadline=text)
            await create_task(update, context, state)
        else:
            await update.message.reply_text("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
    
    elif step == "awaiting_report_text":
        state_manager.update_state(chat_id, reportText=text)
        await submit_report(update, context, state)
    
    elif step == "awaiting_rework_comment":
        state_manager.update_state(chat_id, reworkComment=text)
        await send_task_to_rework(update, context, state)


async def ask_if_photo_needed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Спросить, нужно ли фото к заданию"""
    keyboard = [
        [InlineKeyboardButton("📸 Добавить фото", callback_data="task_photo_yes")],
        [InlineKeyboardButton("⏭️ Продолжить без фото", callback_data="task_photo_no")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Нужно ли добавить фото к заданию?", reply_markup=reply_markup)


async def create_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
    """Создать новое задание"""
    try:
        # Получаем все задания для определения следующего ID
        tasks_data = sheets_service.get_values(SHEET_NAMES['TASKS'])
        next_id = 1
        
        if len(tasks_data) > 1:
            max_id = 0
            for row in tasks_data[1:]:  # Пропускаем заголовок
                if row and row[0]:
                    try:
                        task_id = int(row[0])
                        if task_id > max_id:
                            max_id = task_id
                    except ValueError:
                        continue
            next_id = max_id + 1
        
        # Получаем имя инженера
        engineer_name = auth_service.get_engineer_name(update.effective_chat.id) or "Неизвестный"
        
        # Формируем данные для новой строки
        new_row_data = [
            next_id,                           # Номер
            "Новое",                           # Статус
            state.get('contractor'),           # Подрядчик
            state.get('taskText'),             # Текст задания
            state.get('photoNeeded', False),   # Фото задания
            "",                                # Формула фото
            state.get('deadline', ''),         # Срок выполнения
            "",                                # Текст выполнения
            state.get('photoNeeded', False),   # Фото выполнения
            "",                                # Формула фото выполнения
            engineer_name,                     # Инициатор
            "", "", "", "", ""                  # Остальные поля
        ]
        
        # Добавляем строку в таблицу
        sheets_service.append_row(SHEET_NAMES['TASKS'], new_row_data)
        
        await update.message.reply_text(f"✅ Задание №{next_id} для \"{state.get('contractor')}\" успешно создано.")
        
        state_manager.delete_state(update.effective_chat.id)
        
        # Отправляем меню инженера
        await send_engineer_task_menu(update, context)
        
    except Exception as e:
        logger.error(f"Error in create_task: {e}")
        await update.message.reply_text("❌ Произошла критическая ошибка при создании задания.")


async def submit_report(update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
    """Отправить отчет по заданию"""
    try:
        task_number = state.get('taskNumber')
        
        # Обновляем задание
        updates = {
            "Статус": "На проверке",
            "Текст выполнения": state.get('reportText', ''),
            "Фото выполнения": state.get('reportPhotoFormula', ''),
            "Комментарий инженера": ""
        }
        
        success = await update_task_by_number(task_number, updates)
        
        if success:
            await update.message.reply_text(f"✅ Отчет по заданию №{task_number} успешно отправлен.\n\nЧтобы начать, нажмите /start")
        else:
            await update.message.reply_text(f"❌ Критическая ошибка: не удалось найти задание №{task_number} для обновления.")
        
        state_manager.delete_state(update.effective_chat.id)
        
    except Exception as e:
        logger.error(f"Error in submit_report: {e}")
        await update.message.reply_text("❌ Ошибка при отправке отчета.")


async def update_task_by_number(task_number: str, updates: dict) -> bool:
    """Обновить задание по номеру"""
    try:
        tasks_data = sheets_service.get_values(SHEET_NAMES['TASKS'])
        
        for i, row in enumerate(tasks_data[1:], start=2):  # Начинаем с 2-й строки
            if len(row) > 0 and str(row[0]) == task_number:
                # Обновляем нужные поля
                for field, value in updates.items():
                    # Здесь нужно маппинг полей на индексы колонок
                    if field == "Статус" and len(row) > 1:
                        sheets_service.update_cell(SHEET_NAMES['TASKS'], f"B{i}", value)
                    elif field == "Текст выполнения" and len(row) > 7:
                        sheets_service.update_cell(SHEET_NAMES['TASKS'], f"H{i}", value)
                    elif field == "Фото выполнения" and len(row) > 8:
                        sheets_service.update_cell(SHEET_NAMES['TASKS'], f"I{i}", value)
                    elif field == "Комментарий инженера" and len(row) > 11:
                        sheets_service.update_cell(SHEET_NAMES['TASKS'], f"L{i}", value)
                
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error in update_task_by_number: {e}")
        return False


async def accept_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict, rating: str):
    """Принять выполненное задание"""
    try:
        engineer_name = auth_service.get_engineer_name(update.effective_chat.id) or "Неизвестный"
        
        updates = {
            "Статус": "Выполнено",
            "Оценка": rating,
            "Принял": engineer_name,
            "Дата выполнения": datetime.now().strftime('%d.%m.%Y')
        }
        
        success = await update_task_by_number(state.get('taskNumber'), updates)
        
        if success:
            await update.callback_query.message.reply_text(f"✅ Задание №{state.get('taskNumber')} принято с оценкой {rating}.")
            await send_engineer_task_menu(update, context)
        else:
            await update.callback_query.message.reply_text(f"❌ Критическая ошибка: не удалось найти задание №{state.get('taskNumber')} для обновления.")
        
        state_manager.delete_state(update.effective_chat.id)
        
    except Exception as e:
        logger.error(f"Error in accept_task: {e}")
        await update.callback_query.message.reply_text("❌ Ошибка при принятии задания.")


async def send_task_to_rework(update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
    """Отправить задание на доработку"""
    try:
        task_number = state.get('taskNumber')
        
        updates = {
            "Статус": "На доработке",
            "Комментарий инженера": state.get('reworkComment')
        }
        
        success = await update_task_by_number(task_number, updates)
        
        if success:
            await update.message.reply_text(f"🔄 Задание №{task_number} возвращено подрядчику с комментарием.")
            await send_engineer_task_menu(update, context)
        else:
            await update.message.reply_text(f"❌ Ошибка: не удалось найти задание №{task_number} для обновления.")
        
        state_manager.delete_state(update.effective_chat.id)
        
    except Exception as e:
        logger.error(f"Error in send_task_to_rework: {e}")
        await update.message.reply_text("❌ Ошибка при отправке на доработку.")


async def delete_task_and_renumber(update: Update, context: ContextTypes.DEFAULT_TYPE, task_number: str):
    """Удалить задание и перенумеровать"""
    try:
        # TODO: Реализовать удаление и перенумерацию
        await update.callback_query.message.reply_text(f"✅ Задание №{task_number} удалено.")
        await send_engineer_task_menu(update, context)
        
    except Exception as e:
        logger.error(f"Error in delete_task_and_renumber: {e}")
        await update.callback_query.message.reply_text("❌ Ошибка при удалении задания.")


async def show_task_to_engineer(update: Update, context: ContextTypes.DEFAULT_TYPE, task_number: str, mode: str):
    """Показать задание инженеру"""
    try:
        task_data = await get_task_by_number(task_number)
        
        if not task_data:
            await update.callback_query.message.reply_text("Ошибка: Задание не найдено.")
            return
        
        title = f"Задание №{task_data.get('Номер')} на проверке" if mode == 'review' else f"Задание №{task_data.get('Номер')}"
        
        message = f"<b>{title}</b>\n\n"
        message += f"<b>Подрядчик:</b> {task_data.get('Подрядчик', '')}\n"
        message += f"<b>Текст задания:</b> {task_data.get('Текст задания', '')}\n"
        
        task_photo_link = task_data.get('Фото задания')
        if task_photo_link and task_photo_link.startswith("http"):
            message += f"<b>Фото к заданию:</b> <a href=\"{task_photo_link}\">Посмотреть</a>\n"
        
        message += f"<b>Срок:</b> {task_data.get('Срок выполнения', '')}\n"
        
        if task_data.get('Текст выполнения'):
            message += f"\n<b>ОТЧЕТ ПОДРЯДЧИКА:</b>\n{task_data['Текст выполнения']}"
            report_photo_link = task_data.get('Фото выполнения')
            if report_photo_link and report_photo_link.startswith("http"):
                message += f"\n<b>Фото выполнения:</b> <a href=\"{report_photo_link}\">Посмотреть</a>"
        
        if mode == 'review':
            keyboard = [[
                InlineKeyboardButton("✅ Принять", callback_data=f"task_accept_{task_number}"),
                InlineKeyboardButton("🔄 На доработку", callback_data=f"task_rework_{task_number}")
            ], [
                InlineKeyboardButton("⬅️ К списку заданий", callback_data="engineer_review")
            ]]
        else:
            keyboard = [[
                InlineKeyboardButton("🗑️ Удалить задание", callback_data=f"task_delete_{task_number}")
            ], [
                InlineKeyboardButton("⬅️ Назад к подрядчикам", callback_data="engineer_by_contractor")
            ]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in show_task_to_engineer: {e}")
        await update.callback_query.message.reply_text("❌ Ошибка при получении задания.")


async def handle_tasks_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фото в режиме заданий"""
    chat_id = update.effective_chat.id
    state = state_manager.get_state(chat_id)
    step = state.get('step')
    
    if step == "awaiting_task_photo":
        # TODO: Обработка фото для задания
        await update.message.reply_text("📸 Фото получено. Функция обработки фото в разработке.")
    
    elif step == "awaiting_report_photo":
        # TODO: Обработка фото для отчета
        await update.message.reply_text("📸 Фото отчета получено. Функция обработки фото в разработке.")
