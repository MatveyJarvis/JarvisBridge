@echo off
chcp 65001 >nul
title JarvisBridge Launch Guard (Greeting)

setlocal ENABLEDELAYEDEXPANSION
set "ROOT=C:\JarvisBridge"
set "LOCKFILE=%ROOT%\jarvis.lock"

echo === Jarvis Launch Guard (Greeting) ===
echo.

if exist "%LOCKFILE%" (
    echo ⚠️ Jarvis уже запущен или завершился нештатно.
    echo Если это ошибка — удали файл %LOCKFILE% и повтори запуск.
    pause
    exit /b
)

echo started > "%LOCKFILE%"

echo ✅ Стартую приветствие и hotword...
pushd "%ROOT%"
call .\.venv\Scripts\activate >nul 2>&1
python -X utf8 -u .\start_jarvis_with_greeting.py
popd

del "%LOCKFILE%" >nul 2>&1
echo.
echo 🟢 Jarvis завершил работу. Файл блокировки снят.
pause
endlocal
