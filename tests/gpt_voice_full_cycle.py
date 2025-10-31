# -*- coding: utf-8 -*-
"""
gpt_voice_full_cycle.py — STT -> GPT -> TTS (тихий MCI, без Яндекс.Музыки)
"""
import sys, os, subprocess, wave, time, ctypes
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sounddevice as sd
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from modules.codegpt_bridge import ask_gpt

load_dotenv()
os.makedirs("temp", exist_ok=True)

RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 5
TMP_WAV = "temp\\voice_input.wav"
TTS_MP3 = "temp\\gpt_reply.mp3"

def record_voice():
    print("🎙️ Говори (5 секунд)…")
    data = sd.rec(int(RECORD_SECONDS * RATE), samplerate=RATE, channels=CHANNELS, dtype="int16")
    sd.wait()
    with wave.open(TMP_WAV, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(data.tobytes())
    print("Файл записан:", TMP_WAV)
    return TMP_WAV

def stt_transcribe(wav_path):
    client = OpenAI()
    with open(wav_path, "rb") as f:
        tr = client.audio.transcriptions.create(model="gpt-4o-mini-transcribe", file=f)
    text = tr.text.strip()
    print("🗣️ Распознано:", text)
    return text

# --- ТИХОЕ ВОСПРОИЗВЕДЕНИЕ ЧЕРЕЗ MCI (без окон) ---
_mci = ctypes.windll.winmm.mciSendStringW
def _mci_cmd(cmd):
    buf = ctypes.create_unicode_buffer(255)
    err = _mci(cmd, buf, 254, 0)
    if err != 0:
        raise RuntimeError(f"MCI error {err} on: {cmd}")
    return buf.value

def play_mp3_silent(path):
    path = os.path.abspath(path)
    alias = "gptreply"
    # закрыть, если остался от прошлого запуска
    try: _mci_cmd(f"close {alias}")
    except: pass
    _mci_cmd(f'open "{path}" type mpegvideo alias {alias}')
    _mci_cmd(f"play {alias}")
    # ждём окончания
    while True:
        mode = _mci_cmd(f"status {alias} mode")
        if mode != "playing":
            break
        time.sleep(0.1)
    _mci_cmd(f"close {alias}")

def tts_play(text):
    client = OpenAI()
    # генерим MP3
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts", voice="alloy", input=text
    ) as resp:
        resp.stream_to_file(TTS_MP3)
    size = os.path.getsize(TTS_MP3)
    print(f"🔊 Озвучка готова: {TTS_MP3} | size={size}")
    # играем тихо, без открытия приложений
    play_mp3_silent(TTS_MP3)

def main():
    wav = record_voice()
    user_text = stt_transcribe(wav)
    if not user_text:
        print("Не удалось распознать речь.")
        return
    reply = ask_gpt("Ты — Джарвис, помощник. Отвечай кратко и понятно.", user_text)
    print("\n--- Ответ GPT ---\n", reply, "\n")
    tts_play(reply)

if __name__ == "__main__":
    main()
