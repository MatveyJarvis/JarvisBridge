# play_one_voice.py
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from pydub import AudioSegment
import simpleaudio as sa

ROOT = Path(__file__).parent
OUT = ROOT / "_out"

def play_wav(wav):
    wave = sa.WaveObject.from_wave_file(str(wav))
    p = wave.play()
    p.wait_done()

def main():
    if len(sys.argv) < 2:
        print("usage: python play_one_voice.py <voice>\nvoices: alloy, verse, shimmer, coral, sage")
        return
    v = sys.argv[1].lower()
    mp3 = OUT / f"probe_{v}.mp3"
    if not mp3.exists():
        print(f"no file: {mp3}")
        return
    wav = OUT / f"one_{v}.wav"
    print(f"→ convert {mp3.name} -> {wav.name}")
    AudioSegment.from_file(str(mp3)).export(str(wav), format="wav")
    print("→ play wav…")
    play_wav(wav)
    print("DONE:", v)

if __name__ == "__main__":
    main()
