"""
Планировщик задач для отправки сводок в группу
"""
import asyncio
from datetime import datetime
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config import TELEGRAM_BOT_TOKEN, GROUP_CHAT_ID, SHEET_NAMES
from services.google_sheets import GoogleSheetsService
from logger import logger


def send_headcount_summary():
    """Отправить сводку по численности в группу"""
    try:
        sheets_service = GoogleSheetsService()
        
        # Читаем из "Численность расширенная" - там есть колонка Уведомление
        headcount_data = sheets_service.get_values(SHEET_NAMES.get('HEADCOUNT_EXTENDED', 'Численность расширенная'))
        
        if not headcount_data or len(headcount_data) < 2:
            logger.warning("Нет данных в листе Численность расширенная")
            return
        
        # Ищем колонку с сегодняшней датой
        header = headcount_data[0]
        today = datetime.now().strftime('%d.%m.%Y')
        
        today_idx = None
        for i, val in enumerate(header):
            if str(val).strip() == today:
                today_idx = i
                break
        
        if today_idx is None:
            logger.warning(f"Сегодняшняя дата {today} не найдена в заголовках")
            return
        
        # Собираем данные по организациям
        # Колонки: D=Подрядчик(3), E=Направление(4), F=Смена(5), G=Уведомление(6), today_idx=сегодня
        contractors = {}  # {org: {'notified': bool, 'day': val, 'night': val, 'directions': set}}
        
        for row in headcount_data[1:]:
            if len(row) < 7:
                continue
            
            org = row[3] if len(row) > 3 else ''
            direction = row[4] if len(row) > 4 else ''
            shift = row[5] if len(row) > 5 else ''
            notification = str(row[6]).strip().upper() if len(row) > 6 else 'FALSE'
            today_val_str = row[today_idx] if today_idx < len(row) else ''
            
            if not org:
                continue
            
            if org not in contractors:
                contractors[org] = {'notified': False, 'day': 0, 'night': 0, 'directions': set()}
            
            if notification == 'TRUE':
                contractors[org]['notified'] = True
            
            if direction:
                contractors[org]['directions'].add(direction)
            
            # Парсим числовые значения
            if today_val_str:
                try:
                    val = float(str(today_val_str).replace(',', '.'))
                    if shift == 'День':
                        contractors[org]['day'] += val
                    elif shift == 'Ночь':
                        contractors[org]['night'] += val
                except (ValueError, TypeError):
                    pass
        
        # Формируем сообщение
        today_formatted = datetime.now().strftime('%d.%m.%Y')
        message = f"📊 <b>Сводка по численности за {today_formatted}</b>\n\n"
        
        # Группируем
        notified_with_data = []
        notified_no_data = []
        not_notified = []
        
        for org, info in contractors.items():
            total = info['day'] + info['night']
            dirs = ', '.join(info['directions']) if info['directions'] else ''
            
            if info['notified']:
                if total > 0:
                    notified_with_data.append((org, info['day'], info['night'], dirs))
                else:
                    notified_no_data.append((org, dirs))
            else:
                not_notified.append((org, dirs))
        
        # Кто подал уведомление и есть данные
        message += "✅ <b>Подали уведомление:</b>\n"
        if notified_with_data:
            for org, day, night, dirs in sorted(notified_with_data):
                total = day + night
                if night > 0:
                    message += f"🔹 {org}: <b>{int(day)}/{int(night)}</b> ({dirs})\n"
                else:
                    message += f"🔹 {org}: <b>{int(total)}</b> ({dirs})\n"
        else:
            message += "Нет данных\n"
        
        message += "\n"
        
        # Кто подал уведомление но нет численности
        if notified_no_data:
            message += "⚠️ <b>Подали уведомление, но нет данных:</b>\n"
            for org, dirs in sorted(notified_no_data):
                message += f"🔸 {org} ({dirs})\n"
            message += "\n"
        
        # Кто не подал уведомление
        if not_notified:
            message += "❌ <b>Не подали уведомление:</b>\n"
            for org, dirs in sorted(not_notified):
                message += f"🔴 {org} ({dirs})\n"
        
        # Итоги
        total_day = sum(info['day'] for info in contractors.values())
        total_night = sum(info['night'] for info in contractors.values())
        count_notified = len(notified_with_data) + len(notified_no_data)
        count_not_notified = len(not_notified)
        
        message += f"\n📈 <b>Итого:</b> {int(total_day)}/{int(total_night)} чел.\n"
        message += f"Подали: {count_notified} | Не подали: {count_not_notified}"
        
        # Отправляем в группу
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bot.send_message(chat_id=GROUP_CHAT_ID, text=message, parse_mode='HTML'))
            logger.info(f"Сводка отправлена в группу {GROUP_CHAT_ID}")
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Ошибка отправки сводки: {e}")


def setup_scheduler():
    """Настроить и запустить планировщик"""
    scheduler = BackgroundScheduler(timezone='Asia/Yekaterinburg')
    
    # Сводка в 9:00, 9:30 и 10:00 по Екатеринбургу
    for minute in ['00', '30']:
        scheduler.add_job(
            send_headcount_summary,
            CronTrigger(hour=9, minute=minute, timezone='Asia/Yekaterinburg'),
            id=f'headcount_summary_9_{minute}',
            replace_existing=True
        )
    
    scheduler.add_job(
        send_headcount_summary,
        CronTrigger(hour=10, minute='00', timezone='Asia/Yekaterinburg'),
        id='headcount_summary_10_00',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Scheduler запущен: сводка в 9:00, 9:30, 10:00")
    
    return scheduler
