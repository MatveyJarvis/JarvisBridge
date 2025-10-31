@echo off
setlocal enableextensions
cd /d C:\JarvisBridge

rem === Ждём 15 сек, чтобы поднялись драйверы аудио/сети ===
timeout /t 15 /nobreak >nul

rem === Папка логов ===
if not exist logs mkdir logs

rem === Параметры хотворда (чувствительнее + RU/EN фразы) ===
set HOTWORD_THRESHOLD=0.45
set HOTWORD_PHRASES=привет джарвис;джарвис привет;hey jarvis;hello jarvis
set HOTWORD_LANG=ru-RU
set PYTHONUTF8=1

rem === Активация окружения и быстрый health-check (beep + «Готов к работе») ===
call .venv\Scripts\activate.bat
echo [Watchdog] Startup health...
python -X utf8 -u startup_health.py >> "logs\health_%DATE:~10,4%-%DATE:~4,2%-%DATE:~7,2%.log" 2>&1

:RESTART
echo [Watchdog] Запуск jarvis_hotword.py...
python -X utf8 -u jarvis_hotword.py >> "logs\hotword_%DATE:~10,4%-%DATE:~4,2%-%DATE:~7,2%.log" 2>&1

echo [Watchdog] Процесс завершился. Перезапуск через 5 секунд...
timeout /t 5 /nobreak >nul
goto RESTART
