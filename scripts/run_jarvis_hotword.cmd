@echo off
setlocal enabledelayedexpansion

rem --- определим корень проекта ---
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%\.."
set "PROJECT_ROOT=%CD%"
popd

rem --- активируем виртуальное окружение ---
set "VENV_DIR=%PROJECT_ROOT%\.venv"
if exist "%VENV_DIR%\Scripts\activate.bat" (
    call "%VENV_DIR%\Scripts\activate.bat"
)

cd /d "%PROJECT_ROOT%"

rem --- запускаем hotword-режим ---
if exist "jarvis_hotword.py" (
    python "jarvis_hotword.py"
) else (
    echo [Jarvis] Не найден jarvis_hotword.py в %PROJECT_ROOT%
    timeout /t 5 >nul
)
