# -*- coding: utf-8 -*-
"""
recorder.py — надёжная запись WAV (mono, 16 kHz, 16-bit PCM) для Jarvis.
- Жёсткое приведение типов из .env (никаких 'str' в формулах)
- Безопасное создание папок для выходного файла
- Подробные DEBUG-принты
"""

import os
import wave
import time
import traceback

try:
    import pyaudio
except Exception as e:
    raise RuntimeError("Не установлен pyaudio: pip install pyaudio") from e


def _to_int(name: str, default: int) -> int:
    """Приводит значение из .env к int с дефолтом."""
    v = os.getenv(name, str(default))
    try:
        return int(v)
    except Exception:
        print(f"[WARN] {name}='{v}' не int. Использую {default}")
        return default


def _ensure_outdir(path: str):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def record_wav(seconds: int, out_path: str):
    """
    Записывает аудио с микрофона и сохраняет в WAV (mono, 16kHz, 16-bit).
    seconds: длительность записи в секундах (int)
    out_path: полный путь к выходному WAV
    """

    # ===== Конфиг из .env с безопасным приведением =====
    sample_rate = _to_int("INPUT_SAMPLE_RATE", 16000)     # Глобальный sample rate
    device_index_env = os.getenv("INPUT_DEVICE_INDEX", "").strip()
    device_index = int(device_index_env) if device_index_env.isdigit() else None

    vad_frame_ms = _to_int("VAD_FRAME_MS", 30)            # размер чанка (10/20/30 мс)
    if vad_frame_ms not in (10, 20, 30):
        print(f"[WARN] VAD_FRAME_MS={vad_frame_ms} не из (10,20,30). Ставлю 30.")
        vad_frame_ms = 30

    chunk = int(sample_rate * vad_frame_ms / 1000)        # ← тут раньше и падало
    channels = 1
    sample_width = 2  # 16-bit PCM

    print("[recorder] Конфиг:",
          {"sample_rate": sample_rate, "device_index": device_index,
           "vad_frame_ms": vad_frame_ms, "chunk": chunk, "seconds": seconds})

    _ensure_outdir(out_path)

    pa = pyaudio.PyAudio()
    stream = None
    try:
        # Открываем входной поток
        stream = pa.open(format=pyaudio.paInt16,
                         channels=channels,
                         rate=sample_rate,
                         input=True,
                         input_device_index=device_index,
                         frames_per_buffer=chunk)

        print("[recorder] Открыт поток: mono=True @", sample_rate, "Hz")
        frames = []
        total_chunks = int((seconds * 1000) / vad_frame_ms)

        t0 = time.time()
        for i in range(total_chunks):
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)

        # Закрываем поток
        stream.stop_stream()
        stream.close()
        stream = None

        # Сохраняем WAV
        with wave.open(out_path, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))

        dt = time.time() - t0
        print(f"[recorder] Сохранено: '{out_path}' ({seconds} сек, ~{dt:.2f}s фактически)")
    except Exception:
        print("[recorder][ERROR] Ошибка при записи WAV:")
        traceback.print_exc()
        raise
    finally:
        if stream is not None:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        pa.terminate()
