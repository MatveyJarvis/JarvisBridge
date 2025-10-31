# Jarvis Launcher — run_hotword_plus_main_ru_fast.ps1 (B3)
# — Автоприветствие через отдельный Python-скрипт (scripts/greet_play.py)
# — Дальше стартует ваш голосовой jarvis_hotword.py
# — Без окон (тихий MCI-плеер)

Write-Host "=== Запуск Jarvis ==="
cd C:\JarvisBridge
.\.venv\Scripts\activate

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
chcp 65001 > $null

Write-Host "[Init] Jarvis Bridge Voice Ready"

# Приветствие (TTS → MP3 → MCI)
python -X utf8 -u .\scripts\greet_play.py

# Основной модуль горячего слова (ВАШ реальный голосовой пайплайн)
python -X utf8 -u .\jarvis_hotword.py
