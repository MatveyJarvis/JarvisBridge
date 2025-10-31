# set_openai_voice.py
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ALLOWED = {"alloy","verse","shimmer","coral","sage"}
ENV_PATH = Path(__file__).parent / ".env"

def main():
    if len(sys.argv) < 2:
        print("Использование: python set_openai_voice.py <voice>\nДоступно: alloy, verse, shimmer, coral, sage")
        return
    voice = sys.argv[1].lower()
    if voice not in ALLOWED:
        print(f"❌ Недопустимый голос: {voice}. Доступно: {', '.join(sorted(ALLOWED))}")
        return

    lines = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

    set_model = set_voice = False
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("OPENAI_TTS_MODEL="):
            lines[i] = "OPENAI_TTS_MODEL=gpt-4o-mini-tts"
            set_model = True
        if s.startswith("OPENAI_TTS_VOICE="):
            lines[i] = f"OPENAI_TTS_VOICE={voice}"
            set_voice = True

    if not set_model:
        lines.append("OPENAI_TTS_MODEL=gpt-4o-mini-tts")
    if not set_voice:
        lines.append(f"OPENAI_TTS_VOICE={voice}")

    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ Записано в .env: OPENAI_TTS_MODEL=gpt-4o-mini-tts, OPENAI_TTS_VOICE={voice}")

if __name__ == "__main__":
    main()
