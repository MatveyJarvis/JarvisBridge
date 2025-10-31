@echo off
chcp 65001 >nul
title JarvisBridge Voice Guard

setlocal ENABLEDELAYEDEXPANSION
set "ROOT=C:\JarvisBridge"
set "LOCKFILE=%ROOT%\jarvis.lock"

echo === Jarvis Voice Guard ===
echo.

if exist "%LOCKFILE%" (
    echo ⚠️ Jarvis уже запущен или завершился нештатно.
    echo Если это ошибка — удали файл %LOCKFILE% и повтори запуск.
    pause
    exit /b
)

echo started > "%LOCKFILE%"

echo ✅ Стартую голосовой режим (STT → LLM → TTS)...
pushd "%ROOT%"
call .\.venv\Scripts\activate >nul 2>&1
python -X utf8 -u .\jarvis_main_voice_bridge_v3.py
popd

del "%LOCKFILE%" >nul 2>&1
echo.
echo 🟢 Jarvis завершил работу. Файл блокировки снят.
pause
endlocal
