@echo off
echo ========================================
echo   Первоначальная настройка бота
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не установлен или не добавлен в PATH!
    echo Установите Python 3.8+ с https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python найден
echo.

REM Создание виртуального окружения
if exist "venv\" (
    echo Виртуальное окружение уже существует
) else (
    echo Создание виртуального окружения...
    python -m venv venv
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать виртуальное окружение
        pause
        exit /b 1
    )
    echo [OK] Виртуальное окружение создано
)

echo.

REM Активация виртуального окружения
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Обновление pip
echo.
echo Обновление pip...
python -m pip install --upgrade pip

REM Установка зависимостей
echo.
echo Установка зависимостей из requirements.txt...
pip install -r requirements.txt

if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Установка завершена!
echo ========================================
echo.
echo Следующие шаги:
echo 1. Скопируйте .env.example в .env
echo 2. Заполните .env файл вашими данными
echo 3. Следуйте инструкции в credentials/README.md
echo 4. Запустите бота через run.bat
echo.

deactivate
pause
