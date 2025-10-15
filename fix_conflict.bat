@echo off
echo 🚀 Решение конфликта с Railway ботом
echo =====================================
echo.
echo Выберите вариант решения:
echo.
echo 1. Использовать тестового бота (рекомендуется)
echo 2. Попробовать остановить Railway сервисы
echo 3. Показать инструкции
echo.
set /p choice="Введите номер варианта (1-3): "

if "%choice%"=="1" (
    echo.
    echo 📝 Для использования тестового бота:
    echo 1. Создайте бота через @BotFather в Telegram
    echo 2. Получите токен
    echo 3. Замените 'test_token' в файле local.env
    echo 4. Запустите: python run_local_bot.py
    echo.
    pause
) else if "%choice%"=="2" (
    echo.
    echo 🛑 Пытаемся остановить Railway сервисы...
    python fix_railway_conflict.py
    echo.
    pause
) else if "%choice%"=="3" (
    echo.
    echo 📖 Открываем инструкции...
    start LOCAL_DEVELOPMENT_GUIDE.md
    echo.
    pause
) else (
    echo.
    echo ❌ Неверный выбор. Попробуйте снова.
    echo.
    pause
)
