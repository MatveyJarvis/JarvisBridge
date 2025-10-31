# Jarvis Launcher — run_hotword_plus_main_ru_fast.ps1 (B2)
# — Автоприветствие при старте (через отдельный python-скрипт)
# — Голосовая пауза реализована в jarvis_hotword.py
# — Без окон, тихий MCI-плеер

Write-Host "=== Запуск Jarvis ==="
cd C:\JarvisBridge
.\.venv\Scripts\activate

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
chcp 65001 > $null

Write-Host "[Init] Jarvis Bridge Voice Ready"

# --- Приветствие ---
python -X utf8 - <<EOF
import ctypes, time
from ctypes import wintypes
from openai import OpenAI

_mci = ctypes.windll.winmm.mciSendStringW
def play(path):
    alias = f"tts_{int(time.time()*1000)}"
    _mci(f"close {alias}", None, 0, None)
    _mci(f'open "{path}" type mpegvideo alias {alias}', None, 0, None)
    _mci(f"play {alias} wait", None, 0, None)
    _mci(f"close {alias}", None, 0, None)

client = OpenAI()
mp3 = r"temp\\greet.mp3"
with client.audio.speech.with_streaming_response.create(
    model="gpt-4o-mini-tts",
    voice="alloy",
    input="Привет, я запущен и готов к работе. Жду активацию.",
) as r:
    r.stream_to_file(mp3)
play(mp3)
EOF

# --- Запуск основного hotword-модуля ---
python -X utf8 -u .\jarvis_hotword.py
