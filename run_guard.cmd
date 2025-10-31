@echo off
chcp 65001 >nul
title JarvisBridge Launch Guard

setlocal ENABLEDELAYEDEXPANSION
set "LOCKFILE=C:\JarvisBridge\jarvis.lock"

echo === Jarvis Launch Guard ===
echo.

rem Проверка, запущен ли уже Jarvis
if exist "%LOCKFILE%" (
    echo ⚠️ Jarvis уже запущен или не завершён корректно.
    echo Если это ошибка — удали файл %LOCKFILE%
    echo или перезапусти систему.
    pause
    exit /b
)

rem Создаём lock-файл
echo started > "%LOCKFILE%"

echo ✅ Jarvis стартует...
timeout /t 1 >nul

rem === ТУТ УКАЗЫВАЕМ, ЧТО ИМЕННО ЗАПУСКАТЬ ===
call run_jarvis_hotword.cmd

rem После завершения удаляем lock-файл
del "%LOCKFILE%" >nul 2>&1

echo.
echo 🟢 Jarvis завершил работу. Файл блокировки снят.
pause
endlocal
