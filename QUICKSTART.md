# ⚡ БЫСТРЫЙ СТАРТ - Что нужно сделать прямо сейчас

## ✅ Уже готово (вставлено автоматически):
- Telegram Bot Token
- Gemini API Key  
- Google Drive Folder ID
- Все названия листов

---

## 📋 Осталось 3 шага (10 минут):

### 1. Узнать ID вашей Google таблицы

Откройте вашу таблицу с данными бота в браузере.

URL выглядит так:
```
https://docs.google.com/spreadsheets/d/1abc123xyz456/edit
                                      ↑
                              Это ID таблицы
```

Скопируйте часть между `/d/` и `/edit`

Откройте файл `.env` и замените строку:
```
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
```

На (например):
```
GOOGLE_SPREADSHEET_ID=1abc123xyz456
```

---

### 2. Получить ключ OpenWeatherMap (2 минуты)

1. Откройте https://openweathermap.org/
2. Нажмите "Sign Up" (регистрация бесплатная)
3. Подтвердите email
4. Перейдите в раздел "API keys"
5. Скопируйте ключ

Откройте файл `.env` и замените:
```
OPENWEATHER_API_KEY=your_openweather_api_key_here
```

На:
```
OPENWEATHER_API_KEY=ваш_ключ
```

---

### 3. Настроить Google API (5 минут)

**Важно:** Это нужно для доступа к Google Sheets и Drive

1. Откройте https://console.cloud.google.com/
2. Создайте новый проект (или выберите существующий)
3. В меню слева: **APIs & Services** → **Library**
4. Найдите и включите (кнопка "Enable"):
   - **Google Sheets API**3
   - **Google Drive API**
   - **Generative Language API**

5. Перейдите в **APIs & Services** → **Credentials**
6. Нажмите **Create Credentials** → **OAuth client ID**
7. Если попросит настроить OAuth consent screen:
   - User Type: **External**
   - App name: **Hotel Bot**
   - Ваш email
   - Нажимайте "Save and Continue" до конца

8. Вернитесь к созданию OAuth client ID:
   - Application type: **Desktop app**
   - Name: **Hotel Bot**
   - Нажмите **Create**

9. Нажмите **Download JSON** (кнопка скачивания)
10. Переименуйте скачанный файл в `credentials.json`
11. Поместите в папку `credentials/` (рядом с README.md)

**Подробная инструкция:** см. `credentials/README.md`

---

## 🚀 Запуск

После выполнения 3 шагов выше:

```bash
# 1. Установка (один раз)
setup.bat

# 2. Запуск
run.bat
```

При первом запуске:
- Откроется браузер
- Войдите в Google аккаунт
- Разрешите доступ к Sheets и Drive
- Закройте браузер
- Бот запустится!

---

## ❓ Проблемы?

### "GOOGLE_SPREADSHEET_ID не установлен"
→ Вы не указали ID таблицы в `.env` (шаг 1)

### "OPENWEATHER_API_KEY не установлен"  
→ Вы не получили ключ погоды (шаг 2)

### "credentials.json не найден"
→ Вы не настроили Google API (шаг 3)

### Бот не отвечает
→ Смотрите логи в `logs/bot.log`

---

**Время: ~10 минут**

После этого бот полностью работает! 🎉
