@echo off
setlocal
set "TASK_NAME=Jarvis Watchdog Autostart"
set "RUN_CMD=C:\JarvisBridge\run_jarvis_watchdog.cmd"

rem === Создаём или обновляем задачу: запуск при входе в систему с макс. правами ===
schtasks /Create ^
 /TN "%TASK_NAME%" ^
 /TR "%RUN_CMD%" ^
 /SC ONLOGON ^
 /RL HIGHEST ^
 /F ^
 /RU %USERNAME%

echo [OK] Автостарт настроен: %TASK_NAME%
echo Чтобы запустить сейчас: schtasks /Run /TN "%TASK_NAME%"
pause
