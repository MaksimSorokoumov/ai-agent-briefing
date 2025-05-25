@echo off
echo ========================================
echo    🤖 AI-Агент Брифинга (GUI)
echo ========================================
echo.

echo 📦 Проверка и установка зависимостей...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Ошибка установки зависимостей!
    pause
    exit /b 1
)

echo.
echo ✅ Зависимости установлены успешно!
echo.
echo 🚀 Запуск GUI приложения...
echo.
echo ⚠️  ВАЖНО: Убедитесь, что LM Studio запущен на http://localhost:1234
echo 📋 Инструкции по настройке LM Studio см. в README.md
echo.

python gui_app.py

if %errorlevel% neq 0 (
    echo ❌ Ошибка запуска приложения!
    pause
    exit /b 1
)

pause