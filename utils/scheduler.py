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
        
        headers = extended_data[0]  # Строка 1: Подрядчик, Направление, Смена, Уведомление, даты...
        rows = extended_data[1:]     # Данные
        
        today = datetime.now()
        today_short = today.strftime('%d.%m.%y')  # "24.03.26"
        today_full = today.strftime('%d.%m.%Y')   # "24.03.2026"
        
        # Ищем колонку с сегодняшней датой
        today_col_idx = None
        for i, h in enumerate(headers):
            if h and (h.strip() == today_short or h.strip() == today_full):
                today_col_idx = i
                break
        
        if today_col_idx is None:
            logger.warning(f"⚠️ Сегодняшняя дата ({today_short}) не найдена в заголовках")
            # Пробуем последнюю колонку с датой
            for i in range(len(headers) - 1, -1, -1):
                if headers[i] and '.' in str(headers[i]):
                    today_col_idx = i
                    logger.info(f"Используем последнюю доступную дату: {headers[i]}")
                    break
        
        # Собираем данные: только организации с Уведомление=TRUE
        org_col_idx = None
        direction_col_idx = None
        shift_col_idx = None
        notification_col_idx = None
        
        for i, h in enumerate(headers):
            h_clean = str(h).strip().lower() if h else ''
            if 'подрядчик' in h_clean:
                org_col_idx = i
            elif 'направлен' in h_clean:
                direction_col_idx = i
            elif 'смена' in h_clean:
                shift_col_idx = i
            elif 'уведомлен' in h_clean:
                notification_col_idx = i
        
        if org_col_idx is None or notification_col_idx is None or today_col_idx is None:
            logger.error("⚠️ Не найдены все необходимые колонки в листе")
            return
        
        # Группируем по организациям
        orgs_data = {}  # {org_name: { подано: bool, день: int, ночь: int }}
        
        for row in rows:
            if not row or len(row) <= notification_col_idx:
                continue
            
            org_name = row[org_col_idx].strip() if org_col_idx < len(row) and row[org_col_idx] else ''
            if not org_name:
                continue
            
            # Проверяем флаг мониторинга
            notif_val = row[notification_col_idx].strip().upper() if notification_col_idx < len(row) and row[notification_col_idx] else 'FALSE'
            is_monitored = notif_val in ('TRUE', '1', 'ДА', 'YES')
            
            if not is_monitored:
                continue  # Пропускаем организации без галочки
            
            # Получаем данные за сегодня
            today_val = row[today_col_idx].strip() if today_col_idx < len(row) and row[today_col_idx] else ''
            
            shift = ''
            if shift_col_idx and shift_col_idx < len(row) and row[shift_col_idx]:
                shift = row[shift_col_idx].strip()
            
            # Парсим численность
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
        message = f"📊 <b>Сводка по численности за {today.strftime('%d.%m.%Y')}</b>\n\n"
        
        if not orgs_data:
            message += "⚠️ Нет организаций с активным мониторингом уведомлений"
        else:
            total_day = sum(d['день'] for d in orgs_data.values())
            total_night = sum(d['ночь'] for d in orgs_data.values())
            total = total_day + total_night
            
            message += f"📈 <b>Всего: {int(total)} чел.</b> (☀️ {int(total_day)} / 🌙 {int(total_night)})\n\n"
            
            for org, data in sorted(orgs_data.items()):
                day = int(data['день'])
                night = int(data['ночь'])
                if day > 0 or night > 0:
                    message += f"✅ {org}: ☀️{day} / 🌙{night}\n"
                else:
                    message += f"❌ {org}: <i>нет данных</i>\n"
        
        message += f"\n⏰ {today.strftime('%H:%M')}\n\n📱 Для подачи численности используйте [ТГ-бота](https://t.me/pm_hotel_v3_bot)"
        
        # Отправляем в группу
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.send_message(chat_id=GROUP_CHAT_ID, text=message, parse_mode='HTML'))
        loop.close()
        
        logger.info(f"✅ Сводка отправлена в группу {GROUP_CHAT_ID}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки сводки: {e}")


def setup_scheduler():
    """Настраивает и запускает планировщик"""
    scheduler = BackgroundScheduler(timezone='Asia/Yekaterinburg')
    
    # Сводка в 9:00, 9:30, 10:00
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
