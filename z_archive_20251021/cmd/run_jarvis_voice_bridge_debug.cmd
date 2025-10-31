@echo on
setlocal
cd /d "%~dp0"

REM Покажем, какой Python найден
where python

REM Если есть ваш activate.cmd — активируем среду
if exist "activate.cmd" (
  call activate.cmd
)

REM Принудительно включим UTF-8, запустим подробно, всё в лог
set PYTHONIOENCODING=utf-8
python -X utf8 -u jarvis_main_voice_bridge.py 1>logs\voice_bridge_debug.out.txt 2>logs\voice_bridge_debug.err.txt

echo.
echo === ПРОГРАММА ЗАВЕРШИЛАСЬ ===
echo STDOUT -> logs\voice_bridge_debug.out.txt
echo STDERR -> logs\voice_bridge_debug.err.txt
pause
endlocal
