# play_probe_voices_v2.py
# -*- coding: utf-8 -*-
"""
Проигрывает уже сгенерированные probe_*.mp3 (alloy, verse, shimmer, coral, sage)
из папки _out, конвертирует в WAV и воспроизводит. После — записывает выбор в .env.
Подробные логи на каждом шаге.
"""

import os
import sys
import traceback
from pathlib import Path
from dotenv import load_dotenv
from pydub import AudioSegment
import simpleaudio as sa

ROOT = Path(__file__).parent
OUT = ROOT / "_out"
OUT.mkdir(exist_ok=True)
ENV_PATH = ROOT / ".env"

ORDER = ["alloy", "verse", "shimmer", "coral", "sage"]

def log(msg): 
    print(msg, flush=True)

def play_wav_blocking(wav_path: Path):
    wave_obj = sa.WaveObject.from_wave_file(str(wav_path))
    play_obj = wave_obj.play()
    play_obj.wait_done()

def save_choice_to_env(voice: str):
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

def main():
    load_dotenv()
    print("=== Проигрываю готовые probe_*.mp3 (v2) ===", flush=True)

    # собираем список в нужном порядке
    items = []
    for v in ORDER:
        p = OUT / f"probe_{v}.mp3"
        if p.exists():
            items.append((v, p))
        else:
            log(f"⚠ Нет файла: {p.name} — пропускаю")

    if not items:
        log("❌ Нет ни одного probe_*.mp3. Сначала запусти probe_voices.py.")
        sys.exit(1)

    played = []
    for idx, (voice, mp3p) in enumerate(items, start=1):
        log(f"\n[{idx}/{len(items)}] ▶ {voice}")
        try:
            wavp = OUT / f"probe_play_{voice}.wav"
            audio = AudioSegment.from_file(str(mp3p))
            audio.export(str(wavp), format="wav")
            log(f"— WAV готов: {wavp.name} ({wavp.stat().st_size} байт)")
            log("— Воспроизвожу (simpleaudio)...")
            play_wav_blocking(wavp)
            log(f"DONE:{voice}")
            played.append(voice)
        except Exception as e:
            log(f"❌ Ошибка на голосе {voice}: {e}")
            traceback.print_exc()

    if not played:
        log("\n❌ Ни один файл не удалось воспроизвести.")
        sys.exit(2)

    # выбор
    print("\nДоступны для выбора:")
    for i, v in enumerate(played, start=1):
        print(f"  {i}. {v}")
    raw = input("Ваш выбор (номер или имя): ").strip().lower()

    chosen = None
    if raw.isdigit():
        n = int(raw)
        if 1 <= n <= len(played):
            chosen = played[n-1]
    elif raw in played:
        chosen = raw

    if not chosen:
        print("Некорректный выбор. Ничего не меняю.")
        return

    save_choice_to_env(chosen)
    print(f"✅ В .env установлено: OPENAI_TTS_MODEL=gpt-4o-mini-tts, OPENAI_TTS_VOICE={chosen}")
    print("Готово.")

if __name__ == "__main__":
    main()
