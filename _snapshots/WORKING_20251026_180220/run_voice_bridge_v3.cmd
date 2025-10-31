@echo off
chcp 65001 >nul
title === JARVIS VOICE BRIDGE V3 LAUNCH ===
echo === JARVIS VOICE BRIDGE V3 LAUNCH ===

:: Активируем виртуальную среду
call .venv\Scripts\activate

:: Запускаем основной голосовой мост Jarvis
python -X utf8 -u jarvis_main_voice_bridge_v3.py

pause
