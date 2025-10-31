import os
import queue
import time
import webrtcvad
import numpy as np
import sounddevice as sd
from dataclasses import dataclass
from dotenv import load_dotenv
from collections import deque

load_dotenv()

def _env_int(name, default):
    try:
        return int(os.getenv(name, str(default)).strip())
    except Exception:
        return default

def _env_bool(name, default=False):
    v = os.getenv(name, str(default)).strip().lower()
    return v in ("1", "true", "yes", "on")

@dataclass
class VADConfig:
    sample_rate: int = _env_int("INPUT_SAMPLE_RATE", 16000)
    frame_ms: int = _env_int("VAD_FRAME_MS", 30)            # 10|20|30
    aggressiveness: int = _env_int("VAD_AGGRESSIVENESS", 2) # 0..3
    max_silence_ms: int = _env_int("VAD_MAX_SILENCE_MS", 800)
    pre_roll_ms: int = _env_int("VAD_PRE_ROLL_MS", 300)
    max_record_ms: int = _env_int("VAD_MAX_RECORD_MS", 15000)
    input_device_index: int | None = None
    enabled: bool = _env_bool("VAD_ENABLED", True)

    def __post_init__(self):
        dev = os.getenv("INPUT_DEVICE_INDEX", "").strip()
        if dev != "":
            try:
                self.input_device_index = int(dev)
            except Exception:
                self.input_device_index = None

class VADRecorder:
    """
    Захватывает аудио с микрофона, определяет речь и возвращает PCM16 numpy-буфер.
    - Автостарт по речи
    - Автостоп по тишине
    - Преролл, чтобы не отрезать начало фразы
    - Жёсткий таймаут
    """
    def __init__(self, cfg: VADConfig | None = None):
        self.cfg = cfg or VADConfig()
        if self.cfg.frame_ms not in (10, 20, 30):
            raise ValueError("VAD_FRAME_MS должен быть 10, 20 или 30")
        self.bytes_per_sample = 2  # int16

        self.frame_samples = int(self.cfg.sample_rate * self.cfg.frame_ms / 1000)
        self.frame_bytes = self.frame_samples * self.bytes_per_sample

        self._q = queue.Queue()
        self._vad = webrtcvad.Vad(self.cfg.aggressiveness)

    def _callback(self, indata, frames, time_info, status):
        if status:
            pass
        pcm16 = np.clip(indata[:, 0] * 32768, -32768, 32767).astype(np.int16).tobytes()
        self._q.put(pcm16)

    def record_once(self) -> np.ndarray:
        if not self.cfg.enabled:
            return self._record_fixed_duration(self.cfg.max_record_ms)

        pre_roll_frames = int(self.cfg.pre_roll_ms / self.cfg.frame_ms)
        pre_buffer = deque(maxlen=pre_roll_frames)

        speech_started = False
        silence_ms = 0
        collected = bytearray()
        t_start = time.time()

        with sd.InputStream(
            samplerate=self.cfg.sample_rate,
            channels=1,
            dtype="float32",
            callback=self._callback,
            device=self.cfg.input_device_index,
            blocksize=self.frame_samples
        ):
            while True:
                if (time.time() - t_start) * 1000 >= self.cfg.max_record_ms:
                    break

                try:
                    chunk = self._q.get(timeout=1.0)
                except queue.Empty:
                    continue

                for i in range(0, len(chunk), self.frame_bytes):
                    frame = chunk[i:i+self.frame_bytes]
                    if len(frame) < self.frame_bytes:
                        frame = frame + b'\x00' * (self.frame_bytes - len(frame))

                    is_speech = self._vad.is_speech(frame, self.cfg.sample_rate)

                    if not speech_started:
                        pre_buffer.append(frame)
                        if is_speech:
                            speech_started = True
                            for frm in pre_buffer:
                                collected.extend(frm)
                            silence_ms = 0
                    else:
                        collected.extend(frame
                        )
                        if is_speech:
                            silence_ms = 0
                        else:
                            silence_ms += self.cfg.frame_ms
                            if silence_ms >= self.cfg.max_silence_ms:
                                return np.frombuffer(collected, dtype=np.int16)

        return np.frombuffer(collected, dtype=np.int16)

    def _record_fixed_duration(self, ms: int) -> np.ndarray:
        frames_needed = int(self.cfg.sample_rate * (ms / 1000.0))
        buf = bytearray()
        with sd.InputStream(
            samplerate=self.cfg.sample_rate,
            channels=1,
            dtype="float32",
            callback=self._callback,
            device=self.cfg.input_device_index
        ):
            while len(buf) < frames_needed * self.bytes_per_sample:
                try:
                    buf.extend(self._q.get(timeout=1.0))
                except queue.Empty:
                    pass
        return np.frombuffer(buf, dtype=np.int16)

def pcm16_to_wav_bytes(pcm: np.ndarray, sample_rate: int) -> bytes:
    import io, wave
    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return bio.getvalue()
