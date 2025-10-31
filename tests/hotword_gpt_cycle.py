# -*- coding: utf-8 -*-
# hotword_gpt_cycle.py — 9.5c: WIN_SEC=2.2, DEBOUNCE=1, мягкая калибровка порога
import sys, os, time, re, ctypes, wave
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sounddevice as sd
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from modules.codegpt_bridge import ask_gpt

load_dotenv()
os.makedirs("temp", exist_ok=True)

RATE=16000; CH=1
WIN_SEC=2.2              # было 1.5 — даём времени договорить фразу
DEBOUNCE_NEED=1          # было 2 — теперь достаточно одного попадания
COOLDOWN_SEC=4

TMP_WAKE="temp\\wake.wav"
TMP_CMD ="temp\\cmd.wav"
TTS_MP3 ="temp\\gpt_reply.mp3"

# ---- silent MP3 via MCI ----
_mci = ctypes.windll.winmm.mciSendStringW
def _mci_cmd(cmd):
    buf = ctypes.create_unicode_buffer(255)
    err = _mci(cmd, buf, 254, 0)
    if err != 0: raise RuntimeError(f"MCI error {err} on: {cmd}")
    return buf.value
def play_mp3_silent(path):
    path=os.path.abspath(path); alias="gptreply"
    try: _mci_cmd(f"close {alias}")
    except: pass
    _mci_cmd(f'open "{path}" type mpegvideo alias {alias}')
    _mci_cmd(f"play {alias}")
    while _mci_cmd(f"status {alias} mode")=="playing": time.sleep(0.1)
    _mci_cmd(f"close {alias}")

def tts(text, voice="alloy"):
    client=OpenAI()
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts", voice=voice, input=text
    ) as r:
        r.stream_to_file(TTS_MP3)
    print(f"[TTS] saved {TTS_MP3} size={os.path.getsize(TTS_MP3)}")
    play_mp3_silent(TTS_MP3)

def record_raw(seconds):
    data = sd.rec(int(seconds*RATE), samplerate=RATE, channels=CH, dtype="int16")
    sd.wait()
    return data.reshape(-1)

def save_wav(path, int16_array):
    with wave.open(path,"wb") as wf:
        wf.setnchannels(CH); wf.setsampwidth(2); wf.setframerate(RATE)
        wf.writeframes(int16_array.tobytes())

def rms(int16_array):
    a = int16_array.astype(np.int32)
    return int(np.sqrt(np.mean(a*a)))

def stt(wav_path):
    client=OpenAI()
    with open(wav_path,"rb") as f:
        tr = client.audio.transcriptions.create(model="gpt-4o-mini-transcribe", file=f)
    return (tr.text or "").strip()

_norm = lambda s: re.sub(r"[^a-zа-яё0-9 ]","", s.lower())
def has_wake(text):
    t=_norm(text)
    return ("привет джарвис" in t) or (("джарвис" in t) and ("привет" in t))

def calibrate():
    print("[CAL] тишина 2с…"); bg = record_raw(2.0); bg_rms = rms(bg); print(f"[CAL] шум RMS={bg_rms}")
    print("[CAL] скажи «привет джарвис» 2с…"); sp = record_raw(2.0); sp_rms = rms(sp); print(f"[CAL] речь RMS={sp_rms}")
    # мягкий динамический порог: между шумом и речью, но не выше половины речи
    thr = max(60, min(int(sp_rms*0.5), int(bg_rms*3 + 60)))
    print(f"[CAL] порог RMS_THRESH={thr}")
    return thr

def main():
    print("[RUN] Автокалибровка…")
    RMS_THRESH = calibrate()
    print("[RUN] Скажи: «привет джарвис». Stop: Ctrl+C")

    last_trigger=0.0
    hits=0
    try:
        while True:
            raw = record_raw(WIN_SEC)
            level = rms(raw)
            print(f"[LVL] RMS={level} (thr={RMS_THRESH})")
            if level < RMS_THRESH:
                print("[SKIP] тихо"); hits = 0; continue

            save_wav(TMP_WAKE, raw)
            txt = stt(TMP_WAKE)
            if txt: print("[HEARD]", txt)

            if txt and has_wake(txt):
                hits += 1; print(f"[WAKE#{hits}]")
            else:
                hits = 0

            if hits >= DEBOUNCE_NEED and (time.time()-last_trigger) > COOLDOWN_SEC:
                hits = 0; last_trigger = time.time()
                print("[WAKE] confirmed → СЛУШАЮ…"); tts("Слушаю")
                # запись команды
                raw_cmd = record_raw(5.0); save_wav(TMP_CMD, raw_cmd)
                cmd_txt = stt(TMP_CMD); print("[CMD]", cmd_txt if cmd_txt else "(пусто)")
                if not cmd_txt: tts("Я не расслышал запрос"); continue
                reply = ask_gpt("Ты — Джарвис. Отвечай кратко и по делу.", cmd_txt)
                print("\n[REPLY]\n", reply, "\n"); tts(reply)
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n[STOP] loop finished")

if __name__=="__main__": main()
