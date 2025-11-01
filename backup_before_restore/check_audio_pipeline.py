# check_audio_pipeline.py
# -*- coding: utf-8 -*-
import os, sys, traceback, subprocess
from pathlib import Path
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.utils import which
import simpleaudio as sa

ROOT = Path(__file__).parent
OUT = ROOT / "_out"
OUT.mkdir(exist_ok=True)

def log(msg): print(msg, flush=True)

def main():
    load_dotenv()

    # 1) что видит pydub/ffmpeg
    ffmpeg_path = which("ffmpeg")
    ffprobe_path = which("ffprobe")
    log(f"pydub.which('ffmpeg'): {ffmpeg_path}")
    log(f"pydub.which('ffprobe'): {ffprobe_path}")

    # 2) выбираем исходный mp3
    candidates = [
        OUT / "probe_alloy.mp3",
        OUT / "tts_preview_alloy.mp3",
        OUT / "tts_out.mp3",
    ]
    src = next((p for p in candidates if p.exists()), None)
    if not src:
        log("❌ В _out нет подходящего mp3 (probe_alloy.mp3 / tts_preview_alloy.mp3 / tts_out.mp3).")
        log("   Сначала запусти любой TTS-скрипт, чтобы он создал mp3, и повтори.")
        sys.exit(1)

    log(f"Источник MP3: {src.name} ({src.stat().st_size} байт)")
    wav = OUT / "check_pipeline.wav"

    # 3) пробуем декодировать mp3 -> wav
    try:
        audio = AudioSegment.from_file(str(src))
        audio.export(str(wav), format="wav")
        log(f"✔ Конвертировано в WAV: {wav.name} ({wav.stat().st_size} байт)")
    except Exception as e:
        log("❌ Ошибка конвертации MP3->WAV через pydub/ffmpeg:")
        traceback.print_exc()
        # Попробуем прямым ffmpeg (если есть)
        if ffmpeg_path:
            log("→ Пробую напрямую через ffmpeg...")
            try:
                subprocess.check_call([ffmpeg_path, "-y", "-i", str(src), str(wav)],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                log(f"✔ FFmpeg сконвертировал WAV: {wav.name} ({wav.stat().st_size} байт)")
            except Exception:
                log("❌ Не удалось и через прямой ffmpeg.")
                traceback.print_exc()
                sys.exit(2)
        else:
            sys.exit(2)

    # 4) пробуем проиграть WAV (simpleaudio)
    try:
        log("→ Воспроизвожу check_pipeline.wav (simpleaudio)...")
        wave_obj = sa.WaveObject.from_wave_file(str(wav))
        play_obj = wave_obj.play()
        play_obj.wait_done()
        log("✔ Воспроизведение завершено.")
    except Exception:
        log("❌ Ошибка воспроизведения WAV simpleaudio:")
        traceback.print_exc()
        sys.exit(3)

if __name__ == "__main__":
    main()
