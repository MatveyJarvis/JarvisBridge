@echo off
setlocal enableextensions
cd /d C:\JarvisBridge

rem === Логи ===
if not exist logs mkdir logs

rem === Активация venv ===
call .venv\Scripts\activate.bat

rem === Принудительная UTF-8 и незабуференный вывод ===
set PYTHONUTF8=1

rem === Запуск хотворда с логированием (каждый день — новый файл) ===
python -X utf8 -u jarvis_hotword.py >> "logs\hotword_%DATE:~10,4%-%DATE:~4,2%-%DATE:~7,2%.log" 2>&1
