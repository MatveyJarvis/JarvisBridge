import os
import sys
import subprocess
from dotenv import load_dotenv

# Наш TTS-модуль
import tts_openai

def main():
    load_dotenv()

    # Текст приветствия и скрипт hotword из .env
    greeting_on = os.getenv("GREETING_ON_START", "1").strip() in ("1", "true", "yes", "y")
    greeting_text = os.getenv("GREETING_TEXT", "Привет, Кирилл, готов к работе.").strip()
    hotword_script = os.getenv("HOTWORD_SCRIPT", "jarvis_hotword.py").strip()

    # Озвучка приветствия (голос определяется через .env: TTS_VOICE=alloy)
    if greeting_on and greeting_text:
        try:
            tts_openai.say(greeting_text)
        except Exception as e:
            print(f"[start] TTS greeting error: {e}", file=sys.stderr)

    # Запуск hotword-скрипта тем же процессом Python
    # Важно: используем текущий интерпретатор в активном .venv
    py = sys.executable
    args = [py, "-X", "utf8", "-u", os.path.join(os.getcwd(), hotword_script)]
    print(f"[start] launching hotword: {args!r}")
    # Переносим управление — ждём завершения
    subprocess.call(args)

if __name__ == "__main__":
    main()
