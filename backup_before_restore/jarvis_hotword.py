# -*- coding: utf-8 -*-
"""
jarvis_hotword.py (substring trigger + stable capture)
- Активация по ЛЮБОМУ упоминанию "джарвис"/"jarvis" в фразе.
- Фиксированная запись ~2.8 c без VAD + лёгкое усиление сигнала перед STT.
- После активации hotword освобождает микрофон и ждёт, пока state != active.
"""

import os, io, time, uuid, wave, queue, shutil, subprocess, re
import numpy as np
import sounddevice as sd
from state_control import set_state, get_state

# === .env ===
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
except Exception:
    pass

# --- OpenAI TTS/STT ---
try:
    from openai import OpenAI
    _OPENAI_SDK = "new"
except Exception:
    import openai  # type: ignore
    _OPENAI_SDK = "old"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_STT = os.getenv("OPENAI_STT_MODEL", "whisper-1")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "alloy")

SAMPLE_RATE = int(os.getenv("INPUT_SAMPLE_RATE", "16000"))
_env_idx = os.getenv("INPUT_DEVICE_INDEX", "-1")
DEVICE_INDEX = None if _env_idx in ("-1", "", None) else int(_env_idx)

# ---------- нормализация ----------
_punct_re = re.compile(r"[^\w\s]+", re.UNICODE)
_spaces_re = re.compile(r"\s+")
def _norm(s: str) -> str:
    if not s: return ""
    s = s.lower().replace("ё","е")
    s = _punct_re.sub(" ", s)
    s = _spaces_re.sub(" ", s).strip()
    return s

# --- подстроки, по которым активируемся ---
TRIGGER_SUBSTR = ("джарвис", "jarvis")

# ---------- Recorder (без VAD) ----------
class Recorder:
    def __init__(self, sample_rate=SAMPLE_RATE, device=DEVICE_INDEX):
        self.sr = sample_rate
        self.device = device
        self.q = queue.Queue()
        self.stream = None

    def _callback(self, indata, frames, t, status):
        pcm = (indata[:, 0] * 32767).astype(np.int16).tobytes()
        self.q.put(pcm)

    def start(self):
        if self.stream: return
        self.stream = sd.InputStream(
            samplerate=self.sr, channels=1, dtype="float32",
            blocksize=int(self.sr * 0.03),  # ~30 ms
            device=self.device, callback=self._callback
        )
        self.stream.start()

    def stop(self):
        if self.stream:
            self.stream.stop(); self.stream.close(); self.stream=None
        with self.q.mutex:
            self.q.queue.clear()

    def capture_fixed(self, seconds=2.8) -> bytes:
        need = int(self.sr * seconds) * 2
        buf = bytearray()
        deadline = time.time() + seconds + 1
        while len(buf) < need and time.time() < deadline:
            try:
                buf.extend(self.q.get(timeout=0.4))
            except queue.Empty:
                pass
        return bytes(buf)

# ---------- OpenAI helpers ----------
def _client():
    if not OPENAI_API_KEY: return None
    if _OPENAI_SDK == "new": return OpenAI(api_key=OPENAI_API_KEY)
    else:
        openai.api_key = OPENAI_API_KEY  # type: ignore
        return openai

def _save_wav(path, pcm16, sr=SAMPLE_RATE):
    with wave.open(path,"wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm16)

def stt_ru_with_gain(pcm16: bytes) -> str:
    if not (OPENAI_API_KEY and pcm16): return ""
    # лёгкое автоматическое усиление
    x = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32)
    peak = np.max(np.abs(x)) if x.size else 0
    if peak > 0:
        gain = min(2.5, 1.5 / (peak/32767))
        x = np.clip(x*gain, -32767, 32767)
    pcm16 = x.astype(np.int16).tobytes()

    tmp = os.path.join(os.getcwd(), f"_hot_{uuid.uuid4().hex}.wav")
    _save_wav(tmp, pcm16)
    client = _client()
    try:
        if _OPENAI_SDK == "new":
            with open(tmp,"rb") as f:
                res = client.audio.transcriptions.create(
                    model=MODEL_STT, file=f,
                    response_format="text", temperature=0.0, language="ru"
                )
            return (res or "").strip()
        else:
            with open(tmp,"rb") as f:
                res = client.Audio.transcriptions.create(  # type: ignore
                    model=MODEL_STT, file=f,
                    response_format="text", temperature=0.0, language="ru"
                )
            return (res or "").strip()
    finally:
        try: os.remove(tmp)
        except: pass

def _looks_like_wav(b: bytes)->bool:
    return len(b)>=12 and b[:4]==b"RIFF" and b[8:12]==b"WAVE"

def _ffmpeg_path(): return shutil.which("ffmpeg")

def _convert_to_wav_with_ffmpeg(raw: bytes)->bytes:
    in_p = os.path.join(os.getcwd(), f"tts_in_{uuid.uuid4().hex}.bin")
    out_p= os.path.join(os.getcwd(), f"tts_out_{uuid.uuid4().hex}.wav")
    try:
        with open(in_p,"wb") as f: f.write(raw or b"")
        cmd=[_ffmpeg_path() or "ffmpeg","-hide_banner","-loglevel","error","-y","-i",in_p,"-ac","1","-ar",str(SAMPLE_RATE),out_p]
        subprocess.run(cmd,check=True)
        with open(out_p,"rb") as f: return f.read()
    except Exception as e:
        print(f"[Hotword][TTS] ffmpeg конвертация не удалась: {e}"); return b""
    finally:
        for p in (in_p,out_p):
            try: os.remove(p)
            except: pass

def tts_play(text:str):
    if not (OPENAI_API_KEY and text): return
    client=_client(); raw=b""
    if _OPENAI_SDK=="new":
        res=client.audio.speech.create(model=TTS_MODEL, voice=TTS_VOICE, input=text)
        if hasattr(res,"content") and isinstance(res.content,(bytes,bytearray)): raw=bytes(res.content)
        else:
            try: raw=res.read()  # type: ignore
            except Exception: raw=b""
    else:
        try:
            res = client.audio.speech.create(  # type: ignore
                model=TTS_MODEL, voice=TTS_VOICE, input=text
            ); raw = res.get("content", b"")  # type: ignore
        except Exception: raw=b""
    wav = raw if _looks_like_wav(raw) else _convert_to_wav_with_ffmpeg(raw)
    if not (wav and _looks_like_wav(wav)): return
    with wave.open(io.BytesIO(wav),"rb") as wf:
        sr=wf.getframerate(); ch=wf.getnchannels(); frames=wf.readframes(wf.getnframes())
    pcm=np.frombuffer(frames,dtype=np.int16).astype(np.float32)/32768.0
    pcm=pcm.reshape(-1,ch)
    sd.play(pcm,sr,blocking=True)

# ---------- Main ----------
def main():
    print(f"[Hotword] Использую INPUT_DEVICE_INDEX={DEVICE_INDEX}")
    print("[Hotword] Скажи фразу с упоминанием «Джарвис» (например: «Привет, Джарвис»).")
    rec = Recorder(); rec.start()
    try:
        while True:
            # если main активен — отдаём микрофон
            if get_state() == "active":
                if rec.stream: rec.stop()
                time.sleep(0.2); continue
            if not rec.stream: rec.start()

            pcm = rec.capture_fixed(seconds=2.8)
            if not pcm: continue
            raw = stt_ru_with_gain(pcm); text = _norm(raw)
            if not text: continue
            print(f"[Hotword] Распознано: {raw!r} -> {text!r}   (state={get_state()})")

            if any(sub in text for sub in TRIGGER_SUBSTR):
                set_state("active")
                print("[Hotword] → state: active (передаю управление main)")
                tts_play("Слушаю")
                if rec.stream: rec.stop()
                time.sleep(0.2)
                continue
    except KeyboardInterrupt:
        print("\n[Hotword] Выход")
    finally:
        rec.stop()

if __name__ == "__main__":
    main()
