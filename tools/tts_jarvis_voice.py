# -*- coding: utf-8 -*-
"""
tts_jarvis_voice.py
Исправленная версия (без аргумента format) для новой библиотеки openai.
Голосовой стиль — Jarvis (англ/рус) с постобработкой через ffmpeg.
"""

import os
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:
    raise SystemExit("[ERR] Не найден пакет openai. Установи: pip install openai")

PRESETS = {
    "jarvis_en": {
        "voice": "alloy",
        "fx": [
            "highpass=f=120",
            "lowpass=f=6500",
            "aecho=0.4:0.6:12:0.2",
            "equalizer=f=300:t=h:width=200:g=-3",
            "equalizer=f=3500:t=h:width=800:g=2.5"
        ],
        "sample_text": "Good evening, Kirill. All systems are operational. Awaiting your command."
    },
    "jarvis_ru": {
        "voice": "alloy",
        "fx": [
            "highpass=f=120",
            "lowpass=f=6400",
            "aecho=0.38:0.6:11:0.18",
            "equalizer=f=280:t=h:width=180:g=-2.5",
            "equalizer=f=3300:t=h:width=700:g=2.3"
        ],
        "sample_text": "Добрый вечер, Кирилл. Все системы работают штатно. Ожидаю вашу команду."
    }
}

def _ensure_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

def synth_openai_tts(text: str, voice: str, out_path: Path) -> Path:
    """ Синтез через OpenAI TTS (gpt-4o-mini-tts) в WAV без аргумента format. """
    client = OpenAI()
    tmp_wav = out_path.with_suffix(".dry.wav")
    _ensure_dir(tmp_wav)

    try:
        # Новый API без format=
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text
        ) as response:
            response.stream_to_file(str(tmp_wav))
        return tmp_wav
    except Exception as e:
        print("[WARN] Streaming TTS не сработал, fallback:", e)
        # Фолбэк без format
        resp = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text
        )
        audio_bytes = resp.read() if hasattr(resp, "read") else resp
        with open(tmp_wav, "wb") as f:
            f.write(audio_bytes)
        return tmp_wav

def apply_ffmpeg_fx(in_wav: Path, out_path: Path, filters: list[str]) -> Path:
    _ensure_dir(out_path)
    chain = ",".join(filters)
    cmd = ["ffmpeg", "-y", "-i", str(in_wav), "-af", chain, str(out_path)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        raise SystemExit("[ERR] ffmpeg не найден. Добавь в PATH.")
    return out_path

def main():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("[ERR] В .env нет OPENAI_API_KEY")

    parser = argparse.ArgumentParser()
    parser.add_argument("--text", type=str)
    parser.add_argument("--text_file", type=str)
    parser.add_argument("--preset", type=str, default="jarvis_en", choices=list(PRESETS.keys()))
    parser.add_argument("--out", type=str, default="out/jarvis_sample.wav")
    parser.add_argument("--dry", action="store_true")
    args = parser.parse_args()

    preset = PRESETS[args.preset]
    voice = preset["voice"]

    if args.text:
        text = args.text.strip()
    elif args.text_file:
        with open(args.text_file, "r", encoding="utf-8") as f:
            text = f.read().strip()
    else:
        text = preset["sample_text"]

    out_path = Path(args.out)
    dry_wav = synth_openai_tts(text, voice, out_path)

    if args.dry:
        subprocess.run(["ffmpeg", "-y", "-i", str(dry_wav), str(out_path)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[OK] Чистый TTS сохранён: {out_path}")
        return

    out_final = apply_ffmpeg_fx(dry_wav, out_path, preset["fx"])
    print(f"[OK] Jarvis-style TTS готов: {out_final}")

if __name__ == "__main__":
    main()
