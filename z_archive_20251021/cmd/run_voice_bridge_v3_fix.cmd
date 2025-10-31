@echo off
setlocal
cd /d "%~dp0"
title Jarvis Voice Bridge V3 (fix)

echo === USING PYTHON ===
where python
echo.

REM Активируем venv напрямую (без вашего activate.cmd)
if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
  echo [OK] venv activated
) else (
  echo [WARN] .venv\Scripts\activate.bat не найден. Использую системный Python.
)
echo.

set PYTHONIOENCODING=utf-8
echo === RUNNING jarvis_main_voice_bridge_v3.py ===
python -X utf8 -u "%~dp0jarvis_main_voice_bridge_v3.py"
set EXITCODE=%ERRORLEVEL%
echo.
echo === ПРОГРАММА ЗАВЕРШИЛАСЬ. EXITCODE=%EXITCODE% ===
pause
endlocal
