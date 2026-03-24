"""
Планировщик задач для отправки сводок в группу
"""
import asyncio
from datetime import datetime, timedelta
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import TELEGRAM_BOT_TOKEN, SHEET_NAMES
from services.google_sheets import GoogleSheetsService
from logger import logger

# ID группы для отправки сводок (устанавливается через переменную окружения)
GROUP_CHAT_ID = None  # Будет установлен при первом запуске бота в группе


def set_group_chat_id(chat_id: int):
    """Установить ID группы для отправки сводок"""
    global GROUP_CHAT_ID
    GROUP_CHAT_ID = chat_id
    logger.info(f"✅ GROUP_CHAT_ID установлен: {chat_id}")


async def send_headcount_summary_to_group():
    """Отправить сводку по численности в группу"""
    if not GROUP_CHAT_ID:
        logger.warning("GROUP_CHAT_ID не установлен, сводка не отправлена")
        return
    
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Формируем текст сводки
        message = await build_headcount_summary_message()
        
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message,
            parse_mode='HTML'
        )
        logger.info(f"✅ Сводка отправлена в группу {GROUP_CHAT_ID}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки сводки в группу: {e}")


async def build_headcount_summary_message() -> str:
    """Построить сообщение со сводкой по численности"""
    try:
        sheets_service = GoogleSheetsService()
        headcount_data = sheets_service.get_values(SHEET_NAMES['HEADCOUNT'])
        
        if not headcount_data or len(headcount_data) < 4:
            return "❌ Не удалось получить данные из таблицы численности"
        
        headers = headcount_data[:3]
        rows = headcount_data[3:]
        
        today = datetime.now()
        today_string = today.strftime('%d.%m.%Y')
        
        # Ищем строки за сегодня и за вчера
        today_row = None
        yesterday_row = None
        
        yesterday = today - timedelta(days=1)
        yesterday_string = yesterday.strftime('%d.%m.%Y')
        
        for row in rows:
            if len(row) == 0 or not row[0]:
                continue
            
            date_str = str(row[0]).strip()
            try:
                if len(date_str.split('.')[2]) == 2:
                    row_date = datetime.strptime(date_str, '%d.%m.%y')
                else:
                    row_date = datetime.strptime(date_str, '%d.%m.%Y')
                
                if row_date.strftime('%d.%m.%Y') == today_string:
                    today_row = row
                elif row_date.strftime('%d.%m.%Y') == yesterday_string:
                    yesterday_row = row
            except ValueError:
                continue
        
        def calc_totals(row):
            if not row:
                return 0, 0
            day_total = 0
            night_total = 0
            for i in range(1, len(row)):
                if i >= len(headers[2]):
                    continue
                shift = headers[2][i]
                try:
                    value = float(str(row[i]).replace(',', '.')) if row[i] else 0
                    if shift == 'День':
                        day_total += value
                    elif shift == 'Ночь':
                        night_total += value
                except (ValueError, TypeError):
                    continue
            return day_total, night_total
        
        today_day, today_night = calc_totals(today_row)
        yesterday_day, yesterday_night = calc_totals(yesterday_row)
        
        today_total = today_day + today_night
        yesterday_total = yesterday_day + yesterday_night
        
        # Считаем динамику
        if yesterday_total > 0:
            delta = today_total - yesterday_total
            delta_str = f"({delta:+.0f})" if delta != 0 else "(0)"
        else:
            delta_str = ""
        
        # Собираем данные по организациям
        contractors = {}
        if today_row:
            for i in range(1, len(today_row)):
                if i >= len(headers[0]):
                    continue
                org_name = headers[0][i]
                if not org_name:
                    continue
                
                shift = headers[2][i] if i < len(headers[2]) else ""
                
                try:
                    value = float(str(today_row[i]).replace(',', '.')) if today_row[i] else 0
                except (ValueError, TypeError):
                    value = 0
                
                if org_name not in contractors:
                    contractors[org_name] = {'day': 0, 'night': 0}
                if shift == 'День':
                    contractors[org_name]['day'] += value
                elif shift == 'Ночь':
                    contractors[org_name]['night'] += value
        
        # Формируем сообщение
        message = f"📊 <b>СВОДКА ПО ЧИСЛЕННОСТИ</b>\n"
        message += f"🗓 {today_string}\n\n"
        
        message += f"<b>Сегодня:</b>\n"
        message += f"☀️ День: {today_day:.0f}\n"
        message += f"🌙 Ночь: {today_night:.0f}\n"
        message += f"📈 Всего: {today_total:.0f} {delta_str}\n\n"
        
        if contractors:
            message += "<b>По организациям:</b>\n"
            for org, counts in sorted(contractors.items()):
                if counts['day'] > 0 or counts['night'] > 0:
                    message += f"🔹 {org}: {counts['day']:.0f}/{counts['night']:.0f}\n"
        else:
            message += "<b>Данные по организациям отсутствуют</b>\n"
        
        message += f"\n⏰ Время проверки: {today.strftime('%H:%M')}"
        
        return message
        
    except Exception as e:
        logger.error(f"Ошибка построения сводки: {e}")
        return f"❌ Ошибка формирования сводки: {e}"


def setup_scheduler():
    """Настроить и запустить планировщик"""
    scheduler = AsyncIOScheduler()
    
    # Отправка сводки в 9:00, 9:30 и 10:00
    for minute in ['00', '30']:
        scheduler.add_job(
            send_headcount_summary_to_group,
            CronTrigger(hour=9, minute=minute, timezone='Asia/Yekaterinburg'),
            id=f'headcount_summary_9_{minute}',
            replace_existing=True
        )
    
    scheduler.add_job(
        send_headcount_summary_to_group,
        CronTrigger(hour=10, minute='00', timezone='Asia/Yekaterinburg'),
        id='headcount_summary_10_00',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Scheduler запущен: сводка в 9:00, 9:30, 10:00")
    
    return scheduler
