@echo off
setlocal
REM Тестовый запуск OS-Bridge в режиме консоли (без голоса)

REM Переходим в папку скрипта
cd /d "%~dp0"

REM Активируем venv проекта, если используете (раскомментируйте и поправьте путь):
REM call ..\..\venv\Scripts\activate.bat

python os_bridge.py --cli
endlocal
