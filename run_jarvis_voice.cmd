@echo off
setlocal
chcp 65001 >nul

rem === Путь к твоему проекту (если переносишь — поправь одну строку) ===
set "ROOT=C:\JarvisBridge"

if not exist "%ROOT%" (
  echo [ERROR] Папка проекта не найдена: %ROOT%
  pause
  exit /b 1
)

pushd "%ROOT%"

rem === Проверка виртуального окружения ===
if not exist ".venv\Scripts\activate.bat" (
  echo [ERROR] Не найдено виртуальное окружение: %ROOT%\.venv
  echo Создай его или поправь путь в RUN-скрипте.
  pause
  exit /b 1
)

rem === Активируем venv ===
call ".venv\Scripts\activate.bat"

rem === Чтобы кириллица отображалась корректно ===
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

rem === Запуск Jarvis Voice Bridge ===
python -X utf8 jarvis_main_voice.py

echo(
echo [JarvisBridge] Завершено. Код: %errorlevel%
echo Нажми любую клавишу для закрытия окна...
pause >nul

popd
endlocal
