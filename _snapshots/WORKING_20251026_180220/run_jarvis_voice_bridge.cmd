@echo off
setlocal
cd /d "%~dp0"

REM Если у вас есть свой activate.cmd — используем его.
if exist "activate.cmd" (
  call activate.cmd
)

python jarvis_main_voice_bridge.py
endlocal
