"""
Обработчик модуля "Численность"
"""
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

from services.google_sheets import GoogleSheetsService
from utils.state_manager import state_manager
from utils.auth import auth_service
from utils.validators import is_valid_number
from utils.formatters import format_date
from config import SHEET_NAMES
from logger import logger

sheets_service = GoogleSheetsService()


async def start_headcount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать работу с модулем численности"""
    chat_id = update.effective_chat.id
    user_role = auth_service.get_user_role(chat_id)
    
    state_manager.set_state(chat_id, {'mode': 'headcount'})
    
    if user_role == "ИНЖЕНЕР":
        # Инженеру показываем меню
        keyboard = [
            [InlineKeyboardButton("📝 Внести данные", callback_data="headcount_add")],
            [InlineKeyboardButton("📊 Сводка по численности", callback_data="headcount_summary")],
            [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.message.reply_text(
                "Раздел: Численность",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "Раздел: Численность",
                reply_markup=reply_markup
            )
    else:
        # Подрядчику сразу показываем выбор даты
        await send_date_selection(update, context, "Выберите дату для внесения данных:")


async def send_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    """Отправить выбор даты - только дни текущей недели"""
    # Генерируем кнопки для дней текущей недели (с понедельника по воскресенье)
    keyboard = []
    today = datetime.now()
    
    # Находим понедельник текущей недели
    monday = today - timedelta(days=today.weekday())
    
    for i in range(7):  # 0-6 (понедельник-воскресенье)
        date = monday + timedelta(days=i)
        # Форматируем дату как в таблице: 27.01.26
        date_str = date.strftime('%d.%m.%y')
        day_name = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][i]
        
        button_text = f"{day_name} {date_str}"
        if date.date() == today.date():
            button_text = f"Сегодня ({date_str})"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"date_{date_str}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)


async def handle_headcount_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопок численности"""
    query = update.callback_query
    chat_id = query.from_user.id
    data = query.data
    
    if data == "headcount_add":
        await send_date_selection(update, context, "Выберите дату для внесения данных:")
    
    elif data == "headcount_summary":
        await send_headcount_summary(update, context)
    
    elif data.startswith("date_"):
        date_str = data.split("_", 1)[1]
        state_manager.update_state(chat_id, date=date_str, step="awaiting_org")
        
        # Получаем список организаций из листа "Численность"
        try:
            # Получаем все данные из листа "Численность" для проверки активности
            all_data = sheets_service.get_values(SHEET_NAMES['HEADCOUNT'])
            
            if not all_data or len(all_data) < 4:
                await query.message.reply_text("❌ В таблице численности нет данных или организаций.")
                return
            
            org_row = all_data[0]
            rows = all_data[3:]
            
            today = datetime.now()
            two_weeks_ago = today - timedelta(days=14)
            
            # Группируем колонки по организациям
            org_columns = {}  # {org_name: [indices]}
            for i in range(1, len(org_row)):
                org = org_row[i]
                if org:
                    if org not in org_columns:
                        org_columns[org] = []
                    org_columns[org].append(i)
            
            active_orgs = []
            for org_name, indices in org_columns.items():
                is_active = False
                # Проверяем записи за последние 14 дней
                for row in rows:
                    if not row or not row[0]:
                        continue
                        
                    try:
                        date_val = str(row[0]).strip()
                        if len(date_val.split('.')[2]) == 2:
                            row_date = datetime.strptime(date_val, '%d.%m.%y')
                        else:
                            row_date = datetime.strptime(date_val, '%d.%m.%Y')
                            
                        # Если дата в пределах 14 дней
                        if two_weeks_ago <= row_date <= today:
                            # Проверяем наличие данных в колонках этой организации
                            for idx in indices:
                                if idx < len(row) and row[idx]:
                                    val = str(row[idx]).strip().replace(',', '.')
                                    try:
                                        if float(val) > 0:
                                            is_active = True
                                            break
                                    except ValueError:
                                        continue
                        if is_active:
                            break
                    except (ValueError, IndexError):
                        continue
                
                if is_active:
                    active_orgs.append(org_name)
            
            if not active_orgs:
                await query.message.reply_text("❌ Нет активных организаций (вносивших данные за последние 14 дней).")
                return
            
            keyboard = []
            for org in sorted(active_orgs):
                keyboard.append([InlineKeyboardButton(org, callback_data=f"org_{org}")])
            
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="headcount_add")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("Выберите организацию:", reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error filtering active organizations: {e}")
            await query.message.reply_text("❌ Ошибка при получении списка активных организаций.")
    
    elif data.startswith("org_"):
        org_name = data.split("_", 1)[1]
        state_manager.update_state(chat_id, org=org_name, step="awaiting_dir")
        
        # Получаем направления для организации из листа "Численность"
        try:
            # Получаем заголовки из первых 3 строк листа "Численность"
            headers_data = sheets_service.get_values(
                SHEET_NAMES['HEADCOUNT'],
                '1:3'  # Первые 3 строки: организации, направления, смены
            )
            
            if not headers_data or len(headers_data) < 2:
                await query.message.reply_text(f"❌ Ошибка: для \"{org_name}\" не найдено направлений.")
                return
            
            org_row = headers_data[0]  # Строка 1: организации
            dir_row = headers_data[1]  # Строка 2: направления
            
            # Находим направления для выбранной организации
            dirs_for_org = []
            for i in range(1, len(org_row)):  # Пропускаем первую колонку с датами
                if org_row[i] == org_name and dir_row[i]:
                    dirs_for_org.append(dir_row[i])
            
            # Убираем дубликаты
            unique_dirs = list(set(filter(None, dirs_for_org)))
            
            if not unique_dirs:
                await query.message.reply_text(f"❌ Ошибка: для \"{org_name}\" не найдено направлений.")
                return
            
            keyboard = []
            for dir_name in unique_dirs:
                keyboard.append([InlineKeyboardButton(dir_name, callback_data=f"dir_{dir_name}")])
            
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="headcount_add")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                f'Выбрана организация "{org_name}".\nВыберите направление:',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error getting directions for organization {org_name}: {e}")
            await query.message.reply_text("❌ Ошибка при поиске направлений.")
    
    elif data.startswith("dir_"):
        dir_name = data.split("_", 1)[1]
        state_manager.update_state(chat_id, dir=dir_name, step="awaiting_shift")
        
        keyboard = [
            [
                InlineKeyboardButton("☀️ День", callback_data="shift_День"),
                InlineKeyboardButton("🌙 Ночь", callback_data="shift_Ночь")
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="headcount_add")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Выберите смену:", reply_markup=reply_markup)
    
    elif data.startswith("shift_"):
        shift = data.split("_", 1)[1]
        state_manager.update_state(chat_id, shift=shift, step="awaiting_number")
        
        await query.message.reply_text(
            f'Выбрана смена: "{shift}".\n\n'
            f'Теперь введите численность персонала (только число):'
        )


async def handle_headcount_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений в режиме численности"""
    chat_id = update.effective_chat.id
    text = update.message.text
    state = state_manager.get_state(chat_id)
    
    if state.get('step') == "awaiting_number":
        if is_valid_number(text):
            number = int(float(text))
            
            # Записываем в таблицу
            try:
                await write_data_to_headcount_sheet(update, context, state, number)
                
                state_manager.delete_state(chat_id)
                
                await update.message.reply_text(
                    "Данные сохранены. Используйте кнопки меню для продолжения работы."
                )
            
            except Exception as e:
                logger.error(f"Error saving headcount: {e}")
                await update.message.reply_text(
                    "❌ Произошла ошибка при записи в таблицу. Попробуйте еще раз."
                )
        else:
            await update.message.reply_text(
                "❌ Ошибка. Пожалуйста, введите только число."
            )


async def write_data_to_headcount_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict, number: int):
    """Записать данные численности в Google Sheets"""
    chat_id = update.effective_chat.id
    try:
        # Получаем все данные из листа "Численность"
        all_data = sheets_service.get_values(SHEET_NAMES['HEADCOUNT'])
        
        if not all_data or len(all_data) < 4:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Ошибка: Недостаточно данных в таблице численности."
            )
            return
        
        # Ищем строку с нужной датой
        target_row_index = None
        date_str = state.get('date')
        
        for i in range(3, len(all_data)):  # Начинаем с 4-й строки (индекс 3)
            if all_data[i] and all_data[i][0]:
                # Предполагаем, что дата в формате dd.MM.yyyy
                cell_date = all_data[i][0]
                if isinstance(cell_date, str) and cell_date == date_str:
                    target_row_index = i
                    break
        
        if target_row_index is None:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Ошибка: Дата {date_str} не найдена в таблице."
            )
            return
        
        # Получаем заголовки для поиска нужной колонки
        org_row = all_data[0]  # Строка 1: организации
        dir_row = all_data[1]  # Строка 2: направления
        shift_row = all_data[2]  # Строка 3: смены
        
        # Ищем колонку для записи данных
        target_col_index = None
        org = state.get('org')
        dir = state.get('dir')
        shift = state.get('shift')
        
        for i in range(1, len(org_row)):  # Пропускаем первую колонку с датами
            if (org_row[i] == org and 
                dir_row[i] == dir and 
                shift_row[i] == shift):
                target_col_index = i
                break
        
        if target_col_index is None:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Ошибка: Комбинация \"{org}\" - \"{dir}\" - \"{shift}\" не найдена."
            )
            return
        
        # Записываем значение в таблицу
        # Google Sheets API использует буквенные обозначения колонок (A, B, C...)
        # Но мы используем числовые индексы, поэтому преобразуем
        col_letter = chr(65 + target_col_index)  # 65 = 'A' в ASCII
        row_number = target_row_index + 1  # +1 т.к. в Google Sheets нумерация с 1
        range_notation = f"{col_letter}{row_number}"
        
        sheets_service.update_cell(
            SHEET_NAMES['HEADCOUNT'],
            range_notation,
            number
        )
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f'✅ Готово! Записано значение "{number}" для:\n\n'
                f'📅 Дата: {date_str}\n'
                f'🏢 Организация: {org}\n'
                f'🛠️ Направление: {dir}\n'
                f'🌙 Смена: {shift}'
            )
        )
        
    except Exception as e:
        logger.error(f"Error in write_data_to_headcount_sheet: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Произошла системная ошибка при записи в таблицу."
        )


async def send_headcount_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить сводку по численности (как в GAS)"""
    try:
        await update.callback_query.message.reply_text("⏳ Собираю данные и готовлю сводку, пожалуйста, подождите...")
        
        # Получаем данные из листа "Численность"
        headcount_data = sheets_service.get_values(SHEET_NAMES['HEADCOUNT'])
        
        if not headcount_data or len(headcount_data) < 4:
            await update.callback_query.message.reply_text("❌ Не удалось получить данные.")
            return
        
        # Получаем заголовки
        headers = headcount_data[:3]  # Первые 3 строки
        rows = headcount_data[3:]     # Остальные строки
        
        today = datetime.now()
        today_string = today.strftime('%d.%m.%Y')
        
        # Ищем строку с сегодняшней датой
        today_row = None
        for row in rows:
            if len(row) > 0 and row[0]:
                # Проверяем разные форматы даты
                date_str = str(row[0]).strip()
                try:
                    if '.' in date_str:
                        # Пробуем парсить дату
                        if len(date_str.split('.')[2]) == 2:
                            row_date = datetime.strptime(date_str, '%d.%m.%y')
                        else:
                            row_date = datetime.strptime(date_str, '%d.%m.%Y')
                        
                        if row_date.strftime('%d.%m.%Y') == today_string:
                            today_row = row
                            break
                except ValueError:
                    continue
        
        # Считаем данные за сегодня
        today_day_total = 0
        today_night_total = 0
        contractors = {}  # {org_name: {'day': 0, 'night': 0}}
        
        if today_row:
            # Проходим по всем колонкам (начиная с 1, т.к. 0 - это дата)
            for i in range(1, len(today_row)):
                if i >= len(headers[2]):  # headers[2] - это строка со сменами
                    continue
                    
                org_name = headers[0][i] if i < len(headers[0]) else "Неизвестно"
                shift = headers[2][i]  # Смена из 3-й строки заголовков
                
                if org_name not in contractors:
                    contractors[org_name] = {'day': 0, 'night': 0}
                
                value = 0
                try:
                    if today_row[i]:
                        value = float(str(today_row[i]).replace(',', '.'))
                except (ValueError, TypeError):
                    value = 0
                
                if shift == 'День':
                    today_day_total += value
                    contractors[org_name]['day'] += value
                elif shift == 'Ночь':
                    today_night_total += value
                    contractors[org_name]['night'] += value
        
        today_total = today_day_total + today_night_total
        
        # Считаем среднемесячные данные за текущий год
        monthly_averages = calculate_monthly_averages(rows, headers, today.year)
        
        # Формируем сообщение как в GAS
        message = f"📊 <b>Сводка по численности персонала</b>\n\n"
        message += f"<b><u>Данные за сегодня ({today_string}):</u></b>\n"
        message += f"☀️ Дневная смена: <b>{today_day_total:.0f} чел.</b>\n"
        message += f"🌙 Ночная смена: <b>{today_night_total:.0f} чел.</b>\n"
        message += f"📈 <b>Всего: {today_total:.0f} чел.</b>\n\n"
        
        # Блок по подрядчикам
        message += "<b><u>Подрядчики (день/ночь):</u></b>\n"
        has_contractor_data = False
        for org, counts in contractors.items():
            if counts['day'] > 0 or counts['night'] > 0:
                message += f"🔹 {org}: <b>{counts['day']:.0f}/{counts['night']:.0f}</b>\n"
                has_contractor_data = True
        
        if not has_contractor_data:
            message += "Данные отсутствуют.\n"
            
        message += f"\n<b><u>Среднемесячная ({today.year}):</u></b>\n"
        
        if monthly_averages:
            for month in monthly_averages:
                message += f"{month['name']} - <b>{month['average']:.0f} чел.</b>\n"
        else:
            message += "Данные отсутствуют.\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ Главное меню", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error in send_headcount_summary: {e}")
        await update.callback_query.message.reply_text("❌ Ошибка сводки.")


def calculate_monthly_averages(rows, headers, year):
    """Рассчитать среднемесячные значения (как в GAS)"""
    monthly_data = {}
    month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", 
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    
    for row in rows:
        if len(row) == 0:
            continue
            
        # Проверяем дату в первой колонке
        date_str = str(row[0]).strip() if row[0] else ""
        if not date_str or '.' not in date_str:
            continue
            
        try:
            # Парсим дату
            if len(date_str.split('.')[2]) == 2:
                date_obj = datetime.strptime(date_str, '%d.%m.%y')
            else:
                date_obj = datetime.strptime(date_str, '%d.%m.%Y')
            
            if date_obj.year != year:
                continue
                
            month = date_obj.month - 1  # 0-11 для месяцев
            
            # Считаем сумму за день
            daily_total = 0
            has_data = False
            
            for i in range(1, len(row)):
                try:
                    value = float(str(row[i]).replace(',', '.'))
                    if not (value != value) and value > 0:  # Проверка на NaN
                        daily_total += value
                        has_data = True
                except (ValueError, TypeError):
                    continue
            
            if has_data:
                if month not in monthly_data:
                    monthly_data[month] = {'total': 0, 'count': 0}
                monthly_data[month]['total'] += daily_total
                monthly_data[month]['count'] += 1
                
        except ValueError:
            continue
    
    # Формируем результат
    result = []
    for i in range(12):
        if i in monthly_data:
            average = round(monthly_data[i]['total'] / monthly_data[i]['count'])
            result.append({
                'name': f"{month_names[i]} {year}",
                'average': average
            })
    
    return result
