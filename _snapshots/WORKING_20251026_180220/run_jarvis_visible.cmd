@echo off
REM Jarvis visible runner (COMBO-FAST: main(bg)+hotword(fg))
chcp 65001 >nul
cd /d C:\JarvisBridge

if not exist ".venv\Scripts\activate" (
  echo [ERR] .venv not found: C:\JarvisBridge\.venv\Scripts\activate
  pause
  exit /b 1
)

if not exist "run_hotword_plus_main_ru_fast.ps1" (
  echo [ERR] run_hotword_plus_main_ru_fast.ps1 not found in C:\JarvisBridge
  pause
  exit /b 1
)

echo [OK] Starting COMBO-FAST (visible)...
start "Jarvis (Visible)" powershell -NoProfile -ExecutionPolicy Bypass -NoExit -File ".\run_hotword_plus_main_ru_fast.ps1"
