# Пошаговая инструкция по настройке бота

Эта инструкция поможет вам настроить и запустить Telegram бота с нуля.

## Шаг 1: Установка Python

1. Скачайте Python 3.8 или новее с https://www.python.org/downloads/
2. При установке **обязательно** отметьте "Add Python to PATH"
3. Проверьте установку, открыв командную строку и выполнив:
   ```
   python --version
   ```

## Шаг 2: Создание Telegram бота

1. Откройте Telegram и найдите бота @BotFather
2. Отправьте команду `/newbot`
3. Введите название бота (например, "Hotel Management Bot")
4. Введите username бота (должен заканчиваться на "bot", например, "hotel_mgmt_bot")
5. **Сохраните полученный токен** - он понадобится позже

## Шаг 3: Настройка Google Cloud

### 3.1. Создание проекта

1. Перейдите на https://console.cloud.google.com/
2. Нажмите "Select a project" → "New Project"
3. Введите название проекта (например, "Hotel Bot")
4. Нажмите "Create"

### 3.2. Включение API

1. В меню слева выберите "APIs & Services" → "Library"
2. Найдите и включите следующие API:
   - **Google Sheets API**
   - **Google Drive API**
   - **Generative Language API** (для Gemini)

### 3.3. Создание учетных данных

1. Перейдите в "APIs & Services" → "Credentials"
2. Нажмите "Create Credentials" → "OAuth client ID"
3. Если появится запрос, настройте OAuth consent screen:
   - User Type: External
   - App name: Hotel Bot
   - User support email: ваш email
   - Developer contact: ваш email
   - Нажмите "Save and Continue" до конца
4. Вернитесь к созданию OAuth client ID:
   - Application type: Desktop app
   - Name: Hotel Bot Desktop
5. Нажмите "Create"
6. Скачайте JSON файл (кнопка "Download JSON")
7. Переименуйте файл в `credentials.json`
8. Поместите в папку `credentials/`

## Шаг 4: Получение Gemini API Key

1. Перейдите на https://makersuite.google.com/app/apikey
2. Нажмите "Create API key"
3. Выберите ваш Google Cloud проект
4. Скопируйте ключ

## Шаг 5: Получение OpenWeatherMap API Key

1. Зарегистрируйтесь на https://openweathermap.org/
2. Подтвердите email
3. Перейдите в "API keys"
4. Скопируйте ключ (или создайте новый)

## Шаг 6: Подготовка Google Sheets

1. Откройте вашу существующую таблицу или создайте новую
2. Скопируйте ID таблицы из URL:
   ```
   https://docs.google.com/spreadsheets/d/[ЭТО_ID_ТАБЛИЦЫ]/edit
   ```
3. Убедитесь, что в таблице есть все необходимые листы:
   - Доступ
   - Численность
   - Целевые задания
   - НСЗ
   - Вопросы к заказчику
   - Протокол комплекса строительства
   - БД журнал ПСД
   - logsbot

## Шаг 7: Установка бота

1. Откройте папку с ботом в командной строке:
   ```
   cd C:\Users\nightstalker\Desktop\tgbotHotel
   ```

2. Запустите скрипт установки:
   ```
   setup.bat
   ```

3. Дождитесь завершения установки

## Шаг 8: Настройка конфигурации

1. Скопируйте файл `.env.example` в `.env`:
   ```
   copy .env.example .env
   ```

2. Откройте `.env` в текстовом редакторе (например, Notepad)

3. Заполните все поля:

   ```env
   # Telegram Bot Token (из Шага 2)
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

   # Google Spreadsheet ID (из Шага 6)
   GOOGLE_SPREADSHEET_ID=1abc...xyz

   # Gemini API Key (из Шага 4)
   GEMINI_API_KEY=AIza...

   # OpenWeatherMap API Key (из Шага 5)
   OPENWEATHER_API_KEY=abc123...

   # Остальные параметры можно оставить по умолчанию
   ```

4. Сохраните файл

## Шаг 9: Первый запуск

1. Запустите бота:
   ```
   run.bat
   ```

2. При первом запуске откроется браузер для авторизации Google:
   - Войдите в Google аккаунт, который имеет доступ к таблице
   - Нажмите "Advanced" → "Go to Hotel Bot (unsafe)"
   - Разрешите доступ к Google Sheets и Google Drive
   - Закройте браузер

3. В консоли должно появиться:
   ```
   ✅ Бот успешно запущен и готов к работе!
   ```

## Шаг 10: Проверка работы

1. Откройте Telegram
2. Найдите вашего бота по username
3. Отправьте `/start`
4. Должно появиться главное меню с кнопками

## Шаг 11: Настройка доступа пользователей

1. Откройте Google Sheets таблицу
2. Перейдите на лист "Доступ"
3. Добавьте пользователей:
   - Колонка A: Имя инженера
   - Колонка B: Telegram ID инженера
   - Колонка C: Название организации подрядчика
   - Колонка D: Направление работ
   - Колонка E: Telegram ID подрядчика (можно несколько через запятую)

**Как узнать Telegram ID:**
- Отправьте `/start` боту @userinfobot
- Он покажет ваш ID

## Возможные проблемы

### "Python не найден"
- Переустановите Python с галочкой "Add to PATH"
- Перезагрузите компьютер

### "credentials.json не найден"
- Убедитесь, что файл находится в папке `credentials/`
- Проверьте, что имя файла точно `credentials.json`

### "Invalid token"
- Проверьте правильность токена в `.env`
- Убедитесь, что нет лишних пробелов

### Бот не отвечает
- Проверьте, что бот запущен (окно командной строки открыто)
- Посмотрите логи в `logs/bot.log`

## Автозапуск при старте Windows (опционально)

1. Нажмите Win+R
2. Введите `shell:startup`
3. Создайте ярлык на `run.bat` в этой папке

## Остановка бота

Нажмите `Ctrl+C` в окне командной строки, где запущен бот.

## Обновление бота

Если вы получили новую версию кода:

1. Остановите бота (Ctrl+C)
2. Замените файлы
3. Запустите снова через `run.bat`

---

**Готово!** Ваш бот настроен и готов к работе. 🎉

Если возникли проблемы, проверьте логи в `logs/bot.log` или обратитесь к администратору.
