"""
Планировщик задач для отправки сводок в группу
"""
import asyncio
from datetime import datetime
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from services.google_sheets import GoogleSheetsService
from config import SHEET_NAMES, TELEGRAM_BOT_TOKEN, GROUP_CHAT_ID
from logger import logger


def is_monitoring_org(org_row, idx):
    """Проверяет, мониторится ли организация (есть галочка в колонке Уведомление)"""
    try:
        val = org_row[idx].strip().upper()
        return val == 'TRUE' or val == '1' or val == 'ДА' or val == 'YES'
    except (IndexError, AttributeError):
        return False


def should_send_reminder():
    """Отправляет сводку по численности в группу"""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        sheets = GoogleSheetsService()
        extended_data = sheets.get_values(SHEET_NAMES['HEADCOUNT_EXTENDED'])
        
        if not extended_data or len(extended_data) < 2:
            logger.warning("⚠️ Лист 'Численность расширенная' пуст или слишком мал")
            return
        
        headers = extended_data[0]
        rows = extended_data[1:]
        
        today = datetime.now()
        today_short = today.strftime('%d.%m.%y')
        today_full = today.strftime('%d.%m.%Y')
        
        # Ищем колонку с сегодняшней датой
        today_col_idx = None
        for i, h in enumerate(headers):
            if h and (h.strip() == today_short or h.strip() == today_full):
                today_col_idx = i
                break
        
        if today_col_idx is None:
            logger.warning(f"⚠️ Сегодняшняя дата ({today_short}) не найдена в заголовках")
            for i in range(len(headers) - 1, -1, -1):
                if headers[i] and '.' in str(headers[i]):
                    today_col_idx = i
                    break
        
        # Находим индексы колонок
        org_col_idx = None
        shift_col_idx = None
        notification_col_idx = None
        
        for i, h in enumerate(headers):
            h_clean = str(h).strip().lower() if h else ''
            if 'подрядчик' in h_clean:
                org_col_idx = i
            elif 'смена' in h_clean:
                shift_col_idx = i
            elif 'уведомлен' in h_clean:
                notification_col_idx = i
        
        if org_col_idx is None or notification_col_idx is None or today_col_idx is None:
            logger.error("⚠️ Не найдены все необходимые колонки в листе")
            return
        
        # Собираем данные
        orgs_data = {}
        
        for row in rows:
            if not row or len(row) <= notification_col_idx:
                continue
            
            org_name = row[org_col_idx].strip() if org_col_idx < len(row) and row[org_col_idx] else ''
            if not org_name:
                continue
            
            notif_val = row[notification_col_idx].strip().upper() if notification_col_idx < len(row) and row[notification_col_idx] else 'FALSE'
            is_monitored = notif_val in ('TRUE', '1', 'ДА', 'YES')
            
            if not is_monitored:
                continue
            
            today_val = row[today_col_idx].strip() if today_col_idx < len(row) and row[today_col_idx] else ''
            shift = row[shift_col_idx].strip() if shift_col_idx and shift_col_idx < len(row) and row[shift_col_idx] else ''
            
            try:
                day_value = float(today_val.replace(',', '.')) if today_val else 0
            except (ValueError, AttributeError):
                day_value = 0
            
            if org_name not in orgs_data:
                orgs_data[org_name] = {'день': 0, 'ночь': 0}
            
            if 'ночь' in shift.lower():
                orgs_data[org_name]['ночь'] += day_value
            else:
                orgs_data[org_name]['день'] += day_value
        
        # Формируем сообщение
        message = f"📊 СВОДКА ПО ЧИСЛЕННОСТИ на {today.strftime('%d.%m.%Y')}\n\n"
        
        if not orgs_data:
            message += "⚠️ Нет организаций с активным мониторингом уведомлений"
        else:
            has_data = {org: d for org, d in orgs_data.items() if d['день'] > 0 or d['ночь'] > 0}
            no_data = {org: d for org, d in orgs_data.items() if d['день'] == 0 and d['ночь'] == 0}
            
            message += "ПОДАЛИ ДАННЫЕ:\n"
            for org, data in sorted(has_data.items()):
                d = int(data['день'])
                n = int(data['ночь'])
                message += f"  ✅ {org}: {d}/{n} чел.\n"
            
            message += "\nНЕ ПОДАЛИ:\n"
            for org, data in sorted(no_data.items()):
                message += f"  ❌ {org}\n"
        
        message += f"\nЧтобы подать численность используйте Телеграм бота:\n"
        message += f">>> ПЕРЕЙТИ В ТЕЛЕГРАМ БОТА <<<\n"
        message += "======================================================="
        
        # Отправляем в группу
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.send_message(chat_id=GROUP_CHAT_ID, text=message))
        loop.close()
        
        logger.info(f"✅ Сводка отправлена в группу {GROUP_CHAT_ID}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки сводки: {e}")


def setup_scheduler():
    """Настраивает и запускает планировщик"""
    scheduler = BackgroundScheduler(timezone='Asia/Yekaterinburg')
    
    for hour, minute in [(9, 0), (9, 30), (10, 0)]:
        scheduler.add_job(
            should_send_reminder,
            CronTrigger(hour=hour, minute=minute, timezone='Asia/Yekaterinburg'),
            id=f'headcount_summary_{hour}_{minute}',
            replace_existing=True
        )
    
    scheduler.start()
    logger.info("✅ Scheduler запущен: сводка в 9:00, 9:30, 10:00")
    
    return scheduler
