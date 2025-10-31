# Jarvis Launcher — run_hotword_plus_main_ru_fast.ps1 (C1)
# — Автоприветствие (через scripts/greet_play.py)
# — Голосовая пауза обрабатывается в jarvis_hotword.py
# — Запуск голосового моста (main bridge)
# — Тихий MCI-плеер, без окон

Write-Host "=== Запуск Jarvis (боевой режим C1) ==="

cd C:\JarvisBridge
.\.venv\Scripts\activate
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
chcp 65001 > $null

Write-Host "[Init] Jarvis Bridge Voice Ready"

# — Приветствие
python -X utf8 -u .\scripts\greet_play.py

# — Запуск главного горячего слова в фоновом режиме
Start-Process -NoNewWindow -FilePath "python.exe" -ArgumentList "-X utf8 -u jarvis_hotword.py" -WorkingDirectory "C:\JarvisBridge"

# — Небольшая пауза и запуск основного voice-bridge
Start-Sleep -Seconds 2
python -X utf8 -u .\jarvis_main_voice_bridge_v3.py
