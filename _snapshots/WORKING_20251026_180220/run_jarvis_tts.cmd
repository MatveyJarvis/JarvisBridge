@echo off
cd /d C:\JarvisBridge
if not exist ".venv\Scripts\python.exe" (
  echo [ERR] Не найден виртуальный env: .venv
  echo Сначала активируй/создай .venv и установи зависимости.
  pause
  exit /b 1
)

REM Папка для результатов
if not exist "out" mkdir "out"

REM Пример английского Jarvis
".\.venv\Scripts\python.exe" -X utf8 -u ".\tools\tts_jarvis_voice.py" ^
  --text "Good evening, Kirill. All systems are operational. Awaiting your command." ^
  --preset jarvis_en ^
  --out "out\jarvis_sample_en.wav"

REM Пример русского Jarvis
".\.venv\Scripts\python.exe" -X utf8 -u ".\tools\tts_jarvis_voice.py" ^
  --text "Добрый вечер, Кирилл. Все системы работают штатно. Ожидаю вашу команду." ^
  --preset jarvis_ru ^
  --out "out\jarvis_sample_ru.wav"

echo.
echo [OK] Два файла готовы:
echo   C:\JarvisBridge\out\jarvis_sample_en.wav
echo   C:\JarvisBridge\out\jarvis_sample_ru.wav
echo.
pause
