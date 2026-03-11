@echo off
echo ========================================
echo   Запуск Telegram бота отеля
echo ========================================
echo.

REM Проверка наличия виртуального окружения
if not exist "venv\" (
    echo [ОШИБКА] Виртуальное окружение не найдено!
    echo Сначала выполните setup.bat
    pause
    exit /b 1
)

REM Активация виртуального окружения
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Запуск бота
echo.
echo Запуск бота...
echo.
python bot.py

REM Деактивация при завершении
deactivate

pause
