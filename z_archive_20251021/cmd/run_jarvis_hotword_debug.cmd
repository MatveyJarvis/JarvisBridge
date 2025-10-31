@echo off
chcp 65001 >nul
cd /d C:\JarvisBridge
call .venv\Scripts\activate
python -X utf8 -u jarvis_hotword.py
echo.
echo ==== ПРОГРАММА ЗАВЕРШИЛАСЬ (ошибка или Ctrl+C). Нажми любую клавишу. ====
pause
