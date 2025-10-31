@echo off
chcp 65001 >nul
cd /d C:\JarvisBridge
call .\.venv\Scripts\activate

REM === МИКРОФОН ===
set INPUT_DEVICE_INDEX=1
set INPUT_SAMPLE_RATE=16000

REM === ЯЗЫК и фраза ===
set LANG=ru
set WAKE_PHRASE=привет джарвис

REM === Чувствительность wake-word ===
REM Было thr=72 → делаем мягче
set WAKE_THR=45

REM === VAD / эхо-защита (без изменений) ===
set VAD_AGGRESSIVENESS=3
set MUTE_AFTER_TTS_MS=1800

echo [JARVIS HOTWORD RU] mic=%INPUT_DEVICE_INDEX% sr=%INPUT_SAMPLE_RATE%Hz phrase="%WAKE_PHRASE%" thr=%WAKE_THR%
python -X utf8 -u .\jarvis_hotword.py
pause
