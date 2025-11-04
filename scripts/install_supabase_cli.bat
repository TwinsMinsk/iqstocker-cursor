@echo off
REM Скрипт для установки и настройки Supabase CLI на Windows

echo ============================================================
echo Установка и настройка Supabase CLI
echo ============================================================
echo.

REM Проверка Node.js
echo [1/4] Проверка Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js не установлен!
    echo Пожалуйста, установите Node.js с https://nodejs.org/
    echo После установки запустите этот скрипт снова.
    pause
    exit /b 1
)
echo [OK] Node.js установлен
node --version

REM Проверка возможности установки через Scoop
echo.
echo [2/4] Проверка способов установки...
echo.
echo Supabase CLI больше не поддерживает установку через npm.
echo.
echo Доступные варианты:
echo.
echo [Вариант 1] Использовать через npx (рекомендуется, без установки)
echo   npx supabase --version
echo   npx supabase login
echo.
echo [Вариант 2] Установить через Scoop
echo   1. Установите Scoop:
echo      Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
echo      irm get.scoop.sh ^| iex
echo   2. Установите Supabase CLI:
echo      scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
echo      scoop install supabase
echo.
echo [Вариант 3] Скачать бинарник напрямую
echo   https://github.com/supabase/cli/releases
echo.

REM Проверка через npx
echo Проверка npx...
call npx --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] npx доступен - можно использовать без установки
    call npx supabase --version
    if %errorlevel% equ 0 (
        echo.
        echo [OK] Supabase CLI работает через npx!
        echo.
        echo ============================================================
        echo Рекомендуемый способ использования:
        echo ============================================================
        echo Используйте npx для всех команд Supabase CLI:
        echo   npx supabase login
        echo   npx supabase link --project-ref ваш-project-ref
        echo   npx supabase db execute -f scripts/data/tariff_limits_supabase.sql
        echo ============================================================
        pause
        exit /b 0
    )
)

echo.
echo [3/4] Проверка установленного Supabase CLI...
supabase --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Supabase CLI уже установлен
    supabase --version
    echo.
    echo ============================================================
    echo Следующие шаги:
    echo ============================================================
    echo 1. Выполните: supabase login
    echo 2. Сгенерируйте токен на https://supabase.com/dashboard/account/tokens
    echo 3. Свяжите проект: supabase link --project-ref ваш-project-ref
    echo.
    echo Project ref можно найти в Dashboard ^> Settings ^> General ^> Reference ID
    echo ============================================================
    pause
    exit /b 0
)

echo.
echo [4/4] Supabase CLI не найден
echo.
echo ============================================================
echo Рекомендации:
echo ============================================================
echo 1. Используйте npx (не требует установки):
echo    npx supabase login
echo.
echo 2. Или установите через Scoop:
echo    scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
echo    scoop install supabase
echo.
echo 3. Или используйте Supabase Dashboard для выполнения SQL
echo ============================================================
pause

