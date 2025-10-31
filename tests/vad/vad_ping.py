# -*- coding: utf-8 -*-
import os, sys, time, wave
from datetime import datetime

# Добавляем корень проекта в PYTHONPATH
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Импортируем модуль и функции
import jarvis_hotword_vad as jhv
from jarvis_hotword_vad import VadConfig, record_utterance_vad

# ВРЕМЕННО: отключаем WebRTC-VAD, используем energy-VAD, чтобы быстро проверить цепочку
jhv.USE_WEBRTCVAD = False

# Параметры (слегка строже, но безопасно для energy-VAD)
FRAME_MS        = int(os.getenv("VAD_FRAME_MS", "20"))
MAX_SILENCE_MS  = int(os.getenv("VAD_MAX_SILENCE_MS", "900"))
AGGR            = int(os.getenv("VAD_AGGRESSIVENESS", "3"))   # не влияет на energy-VAD
PREROLL_MS      = int(os.getenv("VAD_PREROLL_MS", "250"))
POSTROLL_MS     = int(os.getenv("VAD_POSTROLL_MS", "300"))
SR              = 16000

print(f"[VAD-PING] (energy) frame={FRAME_MS}ms, max_sil={MAX_SILENCE_MS}ms, pre={PREROLL_MS}ms, post={POSTROLL_MS}ms")

vad_cfg = VadConfig(
    frame_ms=FRAME_MS,
    max_silence_ms=MAX_SILENCE_MS,
    aggressiveness=AGGR,
    preroll_ms=PREROLL_MS,
    postroll_ms=POSTROLL_MS,
)
vad_cfg.samplerate = SR  # 16 кГц

print("[VAD-PING] Говори фразу (1–3 секунды). Запись остановится, когда станет тихо…")
pcm = record_utterance_vad(vad_cfg)

os.makedirs(r"C:\JarvisBridge\temp", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
wav_path = rf"C:\JarvisBridge\temp\vad_ping_{ts}.wav"

with wave.open(wav_path, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)   # 16-bit
    w.setframerate(SR)
    w.writeframes(pcm)

dur_sec = len(pcm) / (SR * 2)
print(f"[OK] Сохранено: {wav_path} | длит.: {dur_sec:.2f} c")
