# -*- coding: utf-8 -*-
"""
Jarvis Voice Bridge v3 (state-aware lazy mic + ALWAYS gpt-4o + stop phrases + TTS auto-convert)
- Микрофон и VAD включаются ТОЛЬКО при state=active.
- Стоп/пауза фразы обрабатываются здесь (после STT, до LLM).
- Логи: stt_done, llm_done, tts_spoken.
"""

import os, io, sys, time, queue, wave, uuid, shutil, subprocess, re
from dataclasses import dataclass

# === .env ===
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
except Exception:
    pass

from state_control import get_state, set_state
from utils.voice_logger import log_turn

# --- АУДИО/ВАД ---
import webrtcvad
import numpy as np
import sounddevice as sd

# --- OPENAI SDK ---
try:
    from openai import OpenAI
    _OPENAI_SDK = "new"
except Exception:
    import openai  # type: ignore
    _OPENAI_SDK = "old"

SAMPLE_RATE        = int(os.getenv("INPUT_SAMPLE_RATE", "16000"))
CHANNELS           = 1
VAD_AGGRESSIVENESS = int(os.getenv("VAD_AGGRESSIVENESS", "2"))
VAD_FRAME_MS       = int(os.getenv("VAD_FRAME_MS", "30"))
MIN_SPEECH_MS      = 600
MAX_CMD_MS         = 9000
CMD_SIL_MS         = 2000
PREROLL_MS         = 700

_device_env = os.getenv("INPUT_DEVICE_INDEX")
DEVICE_INDEX = None if (_device_env is None or _device_env.strip()=="" or _device_env=="-1") else int(_device_env)

MODEL_STT          = os.getenv("OPENAI_STT_MODEL", "whisper-1")
MODEL_LLM_STRONG   = os.getenv("OPENAI_LLM_MODEL_STRONG", "gpt-4o")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
TTS_MODEL          = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
TTS_VOICE          = os.getenv("OPENAI_TTS_VOICE", "alloy")
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY", "")

# --- стоп-фразы (нормализованные) ---
_punct_re  = re.compile(r"[^\w\s]+", re.UNICODE)
_spaces_re = re.compile(r"\s+")
def _norm(s: str) -> str:
    if not s: return ""
    s = s.lower().replace("ё", "е")
    s = _punct_re.sub(" ", s)
    s = _spaces_re.sub(" ", s).strip()
    return s

STOP_PHRASES = {
    "jarvis stop", "jarvis pause",
    "джарвис стоп", "джарвис пауза", "джарвис завершим работу",
    "стоп джарвис", "пауза джарвис", "завершим работу"
}

# =========================
# Вспомогательные сущности
# =========================
@dataclass
class AudioChunk:
    ts: float
    data: bytes

def save_wav(path: str, pcm16: bytes, sample_rate: int = SAMPLE_RATE, channels: int = CHANNELS):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels); wf.setsampwidth(2); wf.setframerate(sample_rate); wf.writeframes(pcm16)

class Recorder:
    def __init__(self, sample_rate=SAMPLE_RATE, channels=CHANNELS, device=DEVICE_INDEX):
        self.sample_rate = sample_rate; self.channels = channels; self.device = device
        self.q = queue.Queue(); self.stream = None

    def _callback(self, indata, frames, t, status):
        pcm = (indata[:, 0] * 32767).astype(np.int16).tobytes()
        self.q.put(AudioChunk(ts=time.time(), data=pcm))

    def start(self):
        if self.stream: return
        self.stream = sd.InputStream(
            samplerate=self.sample_rate, channels=self.channels, dtype="float32",
            blocksize=int(self.sample_rate * (VAD_FRAME_MS/1000.0)),
            device=self.device, callback=self._callback
        )
        self.stream.start()

    def stop(self):
        if self.stream:
            try:
                self.stream.stop(); self.stream.close()
            finally:
                self.stream = None
        with self.q.mutex:
            self.q.queue.clear()

    def read(self, timeout=1.0):
        try: return self.q.get(timeout=timeout)
        except queue.Empty: return None

class VADSession:
    def __init__(self):
        self.vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
        self.frame_bytes       = int(SAMPLE_RATE * (VAD_FRAME_MS/1000.0)) * 2
        self.min_speech_frames = int(MIN_SPEECH_MS / VAD_FRAME_MS)
        self.max_cmd_frames    = int(MAX_CMD_MS   / VAD_FRAME_MS)
        self.silence_frames    = int(CMD_SIL_MS   / VAD_FRAME_MS)
        self.preroll_frames    = int(PREROLL_MS   / VAD_FRAME_MS)

    def is_speech(self, pcm16: bytes) -> bool:
        data = pcm16
        if len(data) != self.frame_bytes:
            if len(data) < self.frame_bytes: data += b"\x00"*(self.frame_bytes-len(data))
            else: data = data[:self.frame_bytes]
        return self.vad.is_speech(data, SAMPLE_RATE)

    def capture_command(self, recorder: "Recorder") -> bytes:
        from collections import deque
        buf=[]; speech_count=0
        preroll=deque(maxlen=self.preroll_frames)

        while True:
            ch = recorder.read(timeout=1.0)
            if ch is None: continue
            preroll.append(ch.data)
            if self.is_speech(ch.data):
                speech_count += 1
                if speech_count >= self.min_speech_frames:
                    buf.extend(preroll); buf.append(ch.data); break
            else:
                speech_count = 0

        total_frames=1; silence_count=0
        while total_frames < self.max_cmd_frames:
            ch = recorder.read(timeout=1.0)
            if ch is None: continue
            buf.append(ch.data); total_frames += 1
            if self.is_speech(ch.data): silence_count = 0
            else:
                silence_count += 1
                if silence_count >= self.silence_frames: break
        return b"".join(buf)

# =========================
# OpenAI helpers
# =========================
def _client():
    if not OPENAI_API_KEY: return None
    if _OPENAI_SDK == "new": return OpenAI(api_key=OPENAI_API_KEY)
    else:
        openai.api_key = OPENAI_API_KEY  # type: ignore
        return openai

def stt_whisper(pcm16: bytes) -> str:
    if not OPENAI_API_KEY: return ""
    client = _client()
    tmp = os.path.join(os.getcwd(), f"temp_stt_{uuid.uuid4().hex}.wav")
    save_wav(tmp, pcm16)
    try:
        if _OPENAI_SDK == "new":
            with open(tmp, "rb") as f:
                res = client.audio.transcriptions.create(
                    model=MODEL_STT, file=f, response_format="text", temperature=0.0
                )
            text = res or ""
        else:
            with open(tmp, "rb") as f:
                res = client.Audio.transcriptions.create(  # type: ignore
                    model=MODEL_STT, file=f, response_format="text", temperature=0.0
                )
            text = res or ""
        return (text or "").strip()
    finally:
        try: os.remove(tmp)
        except: pass

def llm_answer(prompt: str) -> tuple[str,str]:
    if not OPENAI_API_KEY: return "", MODEL_LLM_STRONG
    client = _client(); model = MODEL_LLM_STRONG
    if _OPENAI_SDK == "new":
        res = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Ты вежливый голосовой ассистент Джарвис. Отвечай кратко и по делу."},
                {"role": "user", "content": prompt.strip()},
            ],
            temperature=OPENAI_TEMPERATURE,
        )
        reply = (res.choices[0].message.content or "").strip()
    else:
        res = client.ChatCompletion.create(  # type: ignore
            model=model,
            messages=[
                {"role": "system", "content": "Ты вежливый голосовой ассистент Джарвис. Отвечай кратко и по делу."},
                {"role": "user", "content": prompt.strip()},
            ],
            temperature=OPENAI_TEMPERATURE,
        )
        reply = (res["choices"][0]["message"]["content"] or "").strip()
    return reply, model

def _looks_like_wav(b: bytes) -> bool:
    return len(b) >= 12 and b[:4]==b"RIFF" and b[8:12]==b"WAVE"

def _ffmpeg_path(): return shutil.which("ffmpeg")

def _convert_to_wav_with_ffmpeg(raw_bytes: bytes) -> bytes:
    in_path = os.path.join(os.getcwd(), f"tts_in_{uuid.uuid4().hex}.bin")
    out_path= os.path.join(os.getcwd(), f"tts_out_{uuid.uuid4().hex}.wav")
    try:
        with open(in_path,"wb") as f: f.write(raw_bytes or b"")
        cmd=[_ffmpeg_path() or "ffmpeg","-hide_banner","-loglevel","error","-y","-i",in_path,"-ac","1","-ar",str(SAMPLE_RATE),out_path]
        subprocess.run(cmd, check=True)
        with open(out_path,"rb") as f: return f.read()
    except Exception as e:
        print(f"[TTS] ffmpeg конвертация не удалась: {e}"); return b""
    finally:
        for p in (in_path,out_path):
            try: os.remove(p)
            except: pass

def tts_say(text: str) -> bytes:
    if not (OPENAI_API_KEY and text): return b""
    client = _client()
    raw = b""
    if _OPENAI_SDK == "new":
        res = client.audio.speech.create(model=TTS_MODEL, voice=TTS_VOICE, input=text)
        if hasattr(res,"content") and isinstance(res.content,(bytes,bytearray)):
            raw = bytes(res.content)
        else:
            try: raw = res.read()  # type: ignore
            except Exception: raw = b""
    else:
        try:
            res = client.audio.speech.create(  # type: ignore
                model=TTS_MODEL, voice=TTS_VOICE, input=text
            )
            raw = res.get("content", b"")  # type: ignore
        except Exception: raw = b""
    if raw and _looks_like_wav(raw): return raw
    if not _ffmpeg_path():
        print("[TTS] Получён не-WAV и нет ffmpeg."); return b""
    wav = _convert_to_wav_with_ffmpeg(raw)
    return wav if (wav and _looks_like_wav(wav)) else b""

def play_wav_bytes(wav_bytes: bytes):
    if not wav_bytes: return
    with wave.open(io.BytesIO(wav_bytes),"rb") as wf:
        sr=wf.getframerate(); ch=wf.getnchannels(); frames=wf.readframes(wf.getnframes())
    pcm=np.frombuffer(frames,dtype=np.int16).astype(np.float32)/32768.0
    pcm=pcm.reshape(-1,ch)
    sd.play(pcm,sr,blocking=True)

# =========================
# Основной цикл
# =========================
def main():
    if not OPENAI_API_KEY:
        print("[!] Не найден OPENAI_API_KEY в .env")
    print("[INFO] Jarvis v3 стартует (режим: жду активацию).")
    try:
        play_wav_bytes(tts_say("Привет, я запущен, жду активацию."))
    except Exception:
        pass

    vad = VADSession()
    rec = None
    active_running = False

    try:
        while True:
            st = get_state()

            # Не активен → микрофон должен быть освобождён
            if st != "active":
                if active_running:
                    if rec: rec.stop(); rec = None
                    active_running = False
                time.sleep(0.2)
                continue

            # Активируем захват
            if not active_running:
                rec = Recorder(device=DEVICE_INDEX)
                rec.start()
                active_running = True
                print("[Hotword/VAD] Активен. Произнеси команду…")

            # STT → проверка стоп-фраз → LLM → TTS
            pcm = vad.capture_command(recorder=rec)
            if not pcm:
                continue

            print("[STT] Распознаю…")
            user_text = stt_whisper(pcm)
            print(f"[STT] → {user_text!r}")
            try: log_turn(user_text=user_text, assistant_text="", meta={"stage":"stt_done"})
            except Exception as e: print(f"[LOG] STT: {e}")

            norm = _norm(user_text)

            # --- STOP внутри main ---
            if any(p in norm for p in STOP_PHRASES):
                try:
                    play_wav_bytes(tts_say("Отключаюсь. Скажи Привет Джарвис, чтобы разбудить меня."))
                except Exception:
                    pass
                set_state("paused")
                # цикл заметит state!=active и освободит микрофон
                time.sleep(0.2)
                continue

            if not user_text:
                continue

            print("[LLM] Думаю… (gpt-4o)")
            reply, used_model = llm_answer(user_text)
            print(f"[LLM:{used_model}] → {reply!r}")
            try: log_turn(user_text=user_text, assistant_text=reply, meta={"stage":"llm_done","model":used_model})
            except Exception as e: print(f"[LOG] LLM: {e}")

            print("[TTS] Озвучиваю…")
            wav_bytes = tts_say(reply)
            if wav_bytes:
                try: log_turn(user_text=user_text, assistant_text=reply, meta={"stage":"tts_spoken","model":used_model})
                except Exception as e: print(f"[LOG] TTS: {e}")
            else:
                print("[TTS] Нечего воспроизводить.")
            play_wav_bytes(wav_bytes)

            time.sleep(0.3)

    except KeyboardInterrupt:
        print("\n[INFO] Выход по Ctrl+C")
    finally:
        if rec: rec.stop()
        sd.stop(); sd.wait()

if __name__ == "__main__":
    sys.exit(main())
