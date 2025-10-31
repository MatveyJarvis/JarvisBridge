# -*- coding: utf-8 -*-
"""
tests/hotword_one_shot.py
Один цикл: 3 сек записи -> Whisper (RU) -> печать текста -> если найдено 'джарвис/jarvis' → state=active + озвучка 'Слушаю'.
Сохраняет WAV: C:\JarvisBridge\_hotword_debug.wav
"""

import os, sys, time, wave, uuid, re, io, shutil, subprocess
import numpy as np
import sounddevice as sd

# === Добавляем корень проекта в PYTHONPATH ===
ROOT = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))
if ROOT not in sys.path:
    sys.path.append(ROOT)

# === .env ===
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(ROOT, ".env"))
except Exception:
    pass

# === OpenAI ===
try:
    from openai import OpenAI
    _SDK = "new"
except Exception:
    import openai  # type: ignore
    _SDK = "old"

from state_control import set_state, get_state  # теперь импорт найдётся

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_STT = os.getenv("OPENAI_STT_MODEL", "whisper-1")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "alloy")

SAMPLE_RATE = 16000
_env_idx = os.getenv("INPUT_DEVICE_INDEX", "-1")
DEVICE_INDEX = None if _env_idx in ("-1","",None) else int(_env_idx)

def save_wav(path: str, pcm16: bytes, sr=16000):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm16)

def record_fixed(seconds=3.0) -> bytes:
    q = []
    def cb(indata, frames, t, status):
        q.append((indata[:,0]*32767).astype(np.int16).tobytes())
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                        blocksize=int(SAMPLE_RATE*0.03), device=DEVICE_INDEX, callback=cb):
        time.sleep(seconds)
    return b"".join(q)

def _client():
    if _SDK == "new": return OpenAI(api_key=OPENAI_API_KEY)
    else:
        openai.api_key = OPENAI_API_KEY  # type: ignore
        return openai

def _norm(s: str) -> str:
    s = (s or "").lower().replace("ё","е")
    s = re.sub(r"[^\w\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def stt_ru(p: str) -> str:
    c = _client()
    if _SDK == "new":
        with open(p,"rb") as f:
            r = c.audio.transcriptions.create(model=MODEL_STT, file=f, response_format="text", temperature=0.0, language="ru")
        return (r or "").strip()
    else:
        with open(p,"rb") as f:
            r = c.Audio.transcriptions.create(model=MODEL_STT, file=f, response_format="text", temperature=0.0, language="ru")  # type: ignore
        return (r or "").strip()

def tts_play(text: str):
    if not text: return
    c = _client()
    if _SDK == "new":
        r = c.audio.speech.create(model=TTS_MODEL, voice=TTS_VOICE, input=text)
        data = bytes(getattr(r,"content",b"") or b"")
        if not data:
            try: data = r.read()  # type: ignore
            except Exception: data = b""
    else:
        r = c.audio.speech.create(model=TTS_MODEL, voice=TTS_VOICE, input=text)  # type: ignore
        data = r.get("content", b"")  # type: ignore
    if not data: return
    try:
        with wave.open(io.BytesIO(data),"rb") as wf:
            sr=wf.getframerate(); ch=wf.getnchannels(); frames=wf.readframes(wf.getnframes())
        pcm=np.frombuffer(frames,dtype=np.int16).astype(np.float32)/32768.0
        pcm=pcm.reshape(-1,ch)
        sd.play(pcm, sr, blocking=True)
    except Exception:
        ff = shutil.which("ffmpeg")
        if not ff: return
        in_p = os.path.join(ROOT, f"_tts_in_{uuid.uuid4().hex}.bin")
        out_p= os.path.join(ROOT, f"_tts_out_{uuid.uuid4().hex}.wav")
        try:
            with open(in_p,"wb") as f: f.write(data)
            subprocess.run([ff,"-hide_banner","-loglevel","error","-y","-i",in_p,"-ac","1","-ar",str(SAMPLE_RATE),out_p],check=True)
            with open(out_p,"rb") as f: w=f.read()
            with wave.open(io.BytesIO(w),"rb") as wf:
                sr=wf.getframerate(); ch=wf.getnchannels(); frames=wf.readframes(wf.getnframes())
            pcm=np.frombuffer(frames,dtype=np.int16).astype(np.float32)/32768.0
            pcm=pcm.reshape(-1,ch)
            sd.play(pcm, sr, blocking=True)
        finally:
            for p in (in_p,out_p):
                try: os.remove(p)
                except: pass

def main():
    print(f"[one-shot] INPUT_DEVICE_INDEX={DEVICE_INDEX}")
    print("[one-shot] Запись 3 сек. Скажи: «Привет, Джарвис».")
    pcm = record_fixed(3.0)
    out = os.path.join(ROOT, "_hotword_debug.wav")
    save_wav(out, pcm, SAMPLE_RATE)
    print(f"[one-shot] WAV сохранён: {out}  ({len(pcm)} bytes)")
    if not OPENAI_API_KEY:
        print("[one-shot] Нет OPENAI_API_KEY."); return
    print("[one-shot] Отправляю в Whisper (RU)…")
    try:
        text = stt_ru(out)
    except Exception as e:
        text = f"[EXCEPTION] {type(e).__name__}: {e}"
    print(f"[one-shot] Whisper → {text!r}")
    nt = _norm(text)
    if "джарвис" in nt or "jarvis" in nt:
        print("[one-shot] Триггер найден → state: active")
        set_state("active")
        tts_play("Слушаю")
    else:
        print("[one-shot] Триггера нет. Скажи фразу с «Джарвис».")
    print(f"[one-shot] Текущий state={get_state()}")

if __name__ == "__main__":
    main()
