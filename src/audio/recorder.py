import os
import tempfile
from dotenv import load_dotenv
import numpy as np

from .vad_webrtc import VADRecorder, VADConfig, pcm16_to_wav_bytes

load_dotenv()

def record_wav(output_path: str | None = None) -> str:
    """
    Захватывает аудио с микрофона и сохраняет как WAV (16 kHz, mono, 16-bit).
    Возвращает путь к сохранённому файлу.
    """
    cfg = VADConfig()
    vr = VADRecorder(cfg)
    pcm = vr.record_once()

    # Если тишина — подложим короткую паузу, чтобы последующие шаги не падали
    if pcm.size == 0:
        pcm = np.zeros(int(cfg.sample_rate * 0.2), dtype=np.int16)

    wav_bytes = pcm16_to_wav_bytes(pcm, cfg.sample_rate)

    # Если путь не задан — создаём временный
    if output_path is None:
        fd, path = tempfile.mkstemp(prefix="jarvis_", suffix=".wav")
        os.close(fd)
        output_path = path

    with open(output_path, "wb") as f:
        f.write(wav_bytes)

    return output_path
