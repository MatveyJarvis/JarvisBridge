# tts_openai_preview_voices.py
# -*- coding: utf-8 -*-
"""
OpenAI TTS — предпрослушка и выбор голоса (гарантированно доступные).
Модель: gpt-4o-mini-tts
Проигрывает: alloy, verse, shimmer, coral, sage
soft исключён (на аккаунте не поддерживается).
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
import simpleaudio as sa

ROOT = Path(__file__).parent
OUT = ROOT / "_out"
OUT.mkdir(exist_ok=True)
ENV_PATH = ROOT / ".env"

MODEL = "gpt-4o-mini-tts"
VOICES = ["alloy", "verse", "shimmer", "coral", "sage"]
TEXT = "Привет! Это тестовая фраза для предпрослушки. Оцени тембр, скорость и чёткость дикции."

def client():
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("❌ В .env не найден OPENAI_API_KEY")
    return OpenAI(api_key=key)

def play_wav(path: Path):
    wave = sa.WaveObject.from_wave_file(str(path))
    p = wave.play()
    p.wait_done()

def save_choice(voice: str):
    lines = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    wrote_model = wrote_voice = False
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("OPENAI_TTS_MODEL="):
            lines[i] = f"OPENAI_TTS_MODEL={MODEL}"
            wrote_model = True
        if s.startswith("OPENAI_TTS_VOICE="):
            lines[i] = f"OPENAI_TTS_VOICE={voice}"
            wrote_voice = True
    if not wrote_model:
        lines.append(f"OPENAI_TTS_MODEL={MODEL}")
    if not wrote_voice:
        lines.append(f"OPENAI_TTS_VOICE={voice}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    print("=== OpenAI TTS — предпрослушка голосов ===")
    print(f"Модель: {MODEL}")
    print("Доступные голоса:", ", ".join(VOICES))
    c = client()

    available = []
    for i, v in enumerate(VOICES, start=1):
        print(f"\n[{i}/{len(VOICES)}] ▶ {v}")
        mp3p = OUT / f"tts_preview_{v}.mp3"
        wavp = OUT / f"tts_preview_{v}.wav"
        try:
            with c.audio.speech.with_streaming_response.create(
                model=MODEL, voice=v, input=TEXT
            ) as resp:
                resp.stream_to_file(str(mp3p))
            AudioSegment.from_file(str(mp3p)).export(str(wavp), format="wav")
            play_wav(wavp)
            print(f"✔ Прослушан: {v}")
            available.append(v)
        except Exception as e:
            print(f"⚠ Пропускаю {v}: {e}")

    if not available:
        print("\nНе удалось проиграть ни один голос. Оставляю alloy по умолчанию.")
        save_choice("alloy")
        return

    print("\nВыберите голос (номер или имя):")
    for i, v in enumerate(available, start=1):
        print(f"  {i}. {v}")
    raw = input("Ваш выбор: ").strip().lower()

    chosen = None
    if raw.isdigit():
        n = int(raw)
        if 1 <= n <= len(available):
            chosen = available[n-1]
    elif raw in available:
        chosen = raw

    if not chosen:
        print("❌ Некорректный выбор. Ничего не меняю.")
        return

    save_choice(chosen)
    print(f"✅ Установлено в .env: OPENAI_TTS_MODEL={MODEL}, OPENAI_TTS_VOICE={chosen}")

    # голосовое подтверждение
    try:
        conf_mp3 = OUT / "tts_confirm.mp3"
        conf_wav = OUT / "tts_confirm.wav"
        with c.audio.speech.with_streaming_response.create(
            model=MODEL, voice=chosen, input=f"Голос {chosen} установлен по умолчанию."
        ) as resp:
            resp.stream_to_file(str(conf_mp3))
        AudioSegment.from_file(str(conf_mp3)).export(str(conf_wav), format="wav")
        play_wav(conf_wav)
    except Exception as e:
        print(f"⚠ Подтверждение не удалось: {e}")

    print("Готово.")

if __name__ == "__main__":
    main()
