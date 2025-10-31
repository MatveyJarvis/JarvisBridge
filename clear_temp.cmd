@echo off
chcp 65001 >nul
title JarvisBridge Temp Cleaner
set "TEMP_DIR=C:\JarvisBridge\temp"

echo === Очистка временных аудио-файлов Jarvis ===
echo Папка: %TEMP_DIR%
echo.

if not exist "%TEMP_DIR%" (
    echo [!] Папка temp не найдена.
    pause
    exit /b
)

set /a COUNT=0
for %%F in ("%TEMP_DIR%\*.wav") do (
    del "%%~F" >nul 2>&1
    set /a COUNT+=1
)

echo ✅ Удалено временных .wav файлов: %COUNT%
echo Готово. Постоянные тестовые записи в tests\audio не тронуты.
pause
