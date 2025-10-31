# play_probe_voices.py
# -*- coding: utf-8 -*-
"""
Проигрывает уже сгенерированные probe_*.mp3 (alloy, verse, shimmer, coral, sage)
из папки _out, конвертирует в WAV и воспроизводит.
Затем просит выбрать голос и записывает в .env.
Никакой генерации — только проигрывание готовых файлов.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydub import AudioSegment
import simpleaudio as sa

ROOT = Path(__file__).parent
OUT = ROOT / "_out"
OUT.mkdir(exist_ok=True)
ENV_PATH = ROOT / ".env"

VOICES = ["alloy", "verse", "shimmer", "coral", "sage"]

def play_wav(path: Path):
    wave_obj = sa.WaveObject.from_wave_file(str(path))
    p = wave_obj.play()
    p.wait_done()

def save_choice(voice: str):
    lines = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

    wrote_model = wrote_voice = False
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("OPENAI_TTS_MODEL="):
            lines[i] = "OPENAI_TTS_MODEL=gpt-4o-mini-tts"
            wrote_model = True
        if s.startswith("OPENAI_TTS_VOICE="):
            lines[i] = f"OPENAI_TTS_VOICE={voice}"
            wrote_voice = True

    if not wrote_model:
        lines.append("OPENAI_TTS_MODEL=gpt-4o-mini-tts")
    if not wrote_voice:
        lines.append(f"OPENAI_TTS_VOICE={voice}")

    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    load_dotenv()
    print("=== Проигрываю готовые probe_*.mp3 ===")
    available = []

    for i, v in enumerate(VOICES, start=1):
        candidates = [
            OUT / f"probe_{v}.mp3",             # создавал probe_voices.py
            OUT / f"tts_preview_{v}.mp3",       # вдруг есть из предыдущих попыток
        ]
        src = next((p for p in candidates if p.exists()), None)
        if not src:
            print(f"[{i}] {v}: файла MP3 не найдено → пропускаю.")
            continue

        wav = OUT / f"play_{v}.wav"
        try:
            print(f"[{i}] ▶ {v}")
            AudioSegment.from_file(str(src)).export(str(wav), format="wav")
            play_wav(wav)
            print(f"✔ Прослушан: {v}")
            available.append(v)
        except Exception as e:
            print(f"⚠ Не удалось проиграть {v}: {e}")

    if not available:
        print("\n❌ Нет ни одного готового MP3 для проигрывания. Сначала запусти probe_voices.py.")
        return

    print("\nВыберите голос (номер или имя):")
    for i, v in enumerate(available, start=1):
        print(f"  {i}. {v}")
    choice = input("Ваш выбор: ").strip().lower()

    chosen = None
    if choice.isdigit():
        n = int(choice)
        if 1 <= n <= len(available):
            chosen = available[n-1]
    elif choice in available:
        chosen = choice

    if not chosen:
        print("Некорректный выбор. Ничего не меняю.")
        return

    save_choice(chosen)
    print(f"✅ Установлено в .env: OPENAI_TTS_MODEL=gpt-4o-mini-tts, OPENAI_TTS_VOICE={chosen}")
    print("Готово.")
    
if __name__ == "__main__":
    main()
