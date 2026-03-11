# Telegram Бот для управления строительством отеля

Telegram бот для управления процессами строительства отеля, портированный с Google Apps Script на Python.

## 🎯 Основные функции

- **👷 Численность** - учет персонала по сменам (день/ночь)
- **🎯 Целевые задания** - управление задачами для подрядчиков
- **🗓️ НСЗ** - недельно-суточные задания (в разработке)
- **❓ Вопросы** - система вопросов к заказчику и комплексу
- **📄 Журнал ПСД** - распознавание накладных через Gemini Vision AI
- **☀️ Погода** - прогноз погоды через OpenWeatherMap
- **🔔 Напоминания** - автоматические уведомления (в разработке)

## 📋 Требования

- Python 3.8 или выше
- Google Cloud проект с включенными API (Sheets, Drive, Gemini)
- Telegram Bot Token
- OpenWeatherMap API Key

## 🚀 Быстрый старт

### 1. Установка зависимостей

Запустите скрипт установки:

```bash
setup.bat
```

Или вручную:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Настройка конфигурации

1. Скопируйте `.env.example` в `.env`:
   ```bash
   copy .env.example .env
   ```

2. Откройте `.env` и заполните:
   - `TELEGRAM_BOT_TOKEN` - токен вашего бота от @BotFather
   - `GOOGLE_SPREADSHEET_ID` - ID вашей Google таблицы
   - `GEMINI_API_KEY` - ключ Gemini API
   - `OPENWEATHER_API_KEY` - ключ OpenWeatherMap API

### 3. Настройка Google API

Следуйте инструкции в `credentials/README.md` для получения учетных данных Google.

### 4. Запуск бота

```bash
run.bat
```

Или вручную:

```bash
venv\Scripts\activate
python bot.py
```

## 📁 Структура проекта

```
tgbotHotel/
├── bot.py                  # Главный файл бота
├── config.py               # Конфигурация
├── logger.py               # Логирование
├── requirements.txt        # Зависимости
├── .env                    # Переменные окружения (не в git)
├── .env.example            # Шаблон переменных
│
├── handlers/               # Обработчики модулей
│   ├── main_menu.py
│   ├── headcount.py
│   ├── tasks.py
│   ├── questions.py
│   ├── weather.py
│   └── psd_log.py
│
├── services/               # Сервисы внешних API
│   ├── google_sheets.py
│   ├── google_drive.py
│   ├── gemini_vision.py
│   └── weather_api.py
│
├── utils/                  # Утилиты
│   ├── state_manager.py
│   ├── auth.py
│   ├── validators.py
│   └── formatters.py
│
├── models/                 # Модели данных
├── scheduler/              # Планировщик задач
├── logs/                   # Логи
└── credentials/            # Google API credentials
```

## 🔑 Получение API ключей

### Telegram Bot Token

1. Найдите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен в `.env`

### Google API

См. подробную инструкцию в `credentials/README.md`

### OpenWeatherMap API

1. Зарегистрируйтесь на https://openweathermap.org/
2. Перейдите в API Keys
3. Скопируйте ключ в `.env`

### Gemini API

1. Перейдите на https://makersuite.google.com/app/apikey
2. Создайте API ключ
3. Скопируйте в `.env`

## 🔐 Роли пользователей

Бот поддерживает две роли:

- **ИНЖЕНЕР** - полный доступ ко всем функциям
- **ПОДРЯДЧИК** - ограниченный доступ

Роли настраиваются в Google Sheets на листе "Доступ".

## 📊 Google Sheets структура

Бот работает с следующими листами:

- `Доступ` - роли и права пользователей
- `Численность` - данные о персонале
- `Целевые задания` - задачи для подрядчиков
- `НСЗ` - недельно-суточные задания
- `Вопросы к заказчику` - вопросы
- `Протокол комплекса строительства` - вопросы к комплексу
- `БД журнал ПСД` - журнал проектной документации
- `logsbot` - логи работы бота

## 🐛 Отладка

Логи сохраняются в `logs/bot.log` и дублируются в Google Sheets (лист "logsbot").

Для изменения уровня логирования отредактируйте `LOG_LEVEL` в `.env`:
- `DEBUG` - подробные логи
- `INFO` - основные события
- `WARNING` - предупреждения
- `ERROR` - только ошибки

## ⚙️ Дополнительные настройки

### Изменение города для погоды

В `.env` измените:
```
WEATHER_CITY=Moscow
```

### Настройка времени напоминаний

В `config.py` измените:
```python
REMINDER_DAY_CONTRACTORS = '08:00'
REMINDER_NIGHT_CONTRACTORS = '20:00'
```

## 🆘 Частые проблемы

### Ошибка "TELEGRAM_BOT_TOKEN не установлен"

Убедитесь, что вы создали файл `.env` и заполнили все обязательные поля.

### Ошибка "credentials.json не найден"

Следуйте инструкции в `credentials/README.md` для настройки Google API.

### Бот не отвечает

1. Проверьте, что бот запущен
2. Проверьте логи в `logs/bot.log`
3. Убедитесь, что токен бота правильный

## 📝 Лицензия

Проект для внутреннего использования АО "Прокатмонтаж".

## 👨‍💻 Разработка

Для разработки новых модулей:

1. Создайте обработчик в `handlers/`
2. Зарегистрируйте его в `bot.py`
3. При необходимости создайте сервис в `services/`
4. Добавьте тесты

## 🔄 Обновление

Для обновления зависимостей:

```bash
venv\Scripts\activate
pip install --upgrade -r requirements.txt
```

## 📞 Поддержка

При возникновении проблем обращайтесь к администратору системы.
