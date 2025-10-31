# === run_voice_loop.ps1 — микро-шаг 3.1.2 ===
# Запуск голосового цикла Jarvis (STT → LLM → TTS)
# -----------------------------------------------
cd C:\JarvisBridge

# Активируем виртуальное окружение, если есть
if (Test-Path .\.venv\Scripts\Activate.ps1) {
    . .\.venv\Scripts\Activate.ps1
}

# Запуск основного файла с выводом в консоль
python -X utf8 -u .\jarvis_main_voice_bridge_v3.py
