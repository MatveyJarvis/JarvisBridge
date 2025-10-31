# -*- coding: utf-8 -*-
"""
Jarvis Voice Bridge v3 — микро-шаг 3.1
STT (5 сек записи) -> LLM -> TTS (MP3 через тихий MCI) + лог в logs/voice_dialog.jsonl

Требования окружения:
- Python 3.10+
- Библиотеки: openai, sounddevice, numpy, python-dotenv
- Файловая структура: C:\JarvisBridge\{temp, logs}
- .env с OPENAI_API_KEY и опционально: LLM_MODEL, STT_MODEL, TTS_MODEL, TTS_VOICE
"""
import os
import time
import json
import wave
import uuid
import ctypes
from ctypes import wintypes

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from openai import OpenAI
import webrtcvad

# === Пути ===
ROOT = r"C:\JarvisBridge"
TEMP_DIR = os.path.join(ROOT, "temp")
LOGS_DIR = os.path.join(ROOT, "logs")
AUDIO_IN_WAV = os.path.join(TEMP_DIR, "voice_in.wav")
AUDIO_HW_WAV = os.path.join(TEMP_DIR, "hotword.wav")
AUDIO_OUT_MP3 = os.path.join(TEMP_DIR, "tts_out.mp3")
DIALOG_LOG = os.path.join(LOGS_DIR, "voice_dialog.jsonl")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# === .env ===
load_dotenv(os.path.join(ROOT, ".env"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY не найден в .env")

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")
STT_MODEL = os.getenv("STT_MODEL", "whisper-1")
TTS_MODEL = os.getenv("TTS_MODEL", "gpt-4o-mini-tts")
TTS_VOICE = os.getenv("TTS_VOICE", "alloy")

HOTWORD = os.getenv("HOTWORD", "джарвис")
# === Аудио запись ===
SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 5

client = OpenAI(api_key=OPENAI_API_KEY)

# === Тихое воспроизведение MP3 через MCI ===
mciSendStringW = ctypes.windll.winmm.mciSendStringW
mciSendStringW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.UINT, wintypes.HANDLE]
mciSendStringW.restype = wintypes.UINT

def _mci(cmd: str) -> None:
    buf = ctypes.create_unicode_buffer(1024)
    err = mciSendStringW(cmd, buf, 1024, 0)
    if err != 0:
        print(f"[MCI] error {err} on: {cmd}")

def play_mp3_mci(path: str) -> None:
    alias = f"mp3_{uuid.uuid4().hex}"
    _mci(f'open "{path}" type mpegvideo alias {alias}')
    _mci(f"play {alias} wait")
    _mci(f"close {alias}")

def record_wav(path: str, seconds: float = RECORD_SECONDS, rate: int = SAMPLE_RATE, channels: int = CHANNELS) -> None:
    print(f"[rec] start {seconds}s @ {rate} Hz, channels={channels}")
    audio = sd.rec(int(seconds * rate), samplerate=rate, channels=channels, dtype="int16")
    sd.wait()
    print("[rec] stop")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(audio.tobytes())
    print(f"[rec] saved: {path}")

def record_wav_vad(path: str, rate: int = SAMPLE_RATE, channels: int = CHANNELS) -> None:
    '''
    Запись с автостартом/автостопом по голосу (WebRTC VAD).
    - старт после первых явно озвученных кадров
    - стоп после ~0.4 сек тишины (и минимум ~0.3 сек речи)
    - ограничение записи не более 10 сек
    Сохраняем WAV (16-bit PCM, mono @ 16 kHz).
    '''
    print("[vad] listen… (автостарт/стоп)")
    vad = webrtcvad.Vad(2)  # 0..3 (агрессивность)
    frame_ms = 20
    samples_per_frame = int(rate * frame_ms / 1000)       # 320
    max_frames = int(10_000 / frame_ms)                   # <= 10 c
    min_speech_frames = int(300 / frame_ms)               # >= 0.3 c для валидного куска
    silence_stop_frames = int(600 / frame_ms)             # 0.4 c тишины -> стоп
    pre_roll_frames = int(300 / frame_ms)                 # 0.3 c доречевого буфера

    import collections
    pre = collections.deque(maxlen=pre_roll_frames)
    captured = []
    started = False
    voiced_streak = 0
    silence_streak = 0

    with sd.RawInputStream(samplerate=rate, channels=channels, dtype='int16', blocksize=samples_per_frame) as stream:
        for i in range(max_frames):
            data, ovf = stream.read(samples_per_frame)  # bytes
            b = bytes(data)
            is_voiced = vad.is_speech(b, rate)

            if not started:
                pre.append(b)
                voiced_streak = voiced_streak + 1 if is_voiced else 0
                if voiced_streak >= 2:  # ~40 мс голоса
                    started = True
                    captured.extend(list(pre))
                    pre.clear()
                    silence_streak = 0
                    print("[vad] rec start")
                continue

            captured.append(b)
            if is_voiced:
                silence_streak = 0
            else:
                silence_streak += 1

            if silence_streak >= silence_stop_frames and len(captured) >= min_speech_frames:
                print("[vad] rec stop (silence)")
                break
        else:
            print("[vad] rec stop (timeout)")

    if not captured:\n        # гарантированный минимум 0.3 c «тишины»\n        min_frames = int(300 / frame_ms)\n        captured = [b"\\x00\\x00"] * (samples_per_frame * min_frames)  # короткая «тишина», чтобы не падать

    raw = b"".join(captured)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(raw)
    print(f"[rec] saved (VAD): {path}")
def _norm_text(s: str) -> str:
    return (s or '').strip().lower().replace('ё','е')

def wait_hotword() -> str:
    '''
    Цикл ожидания горячего слова (VAD+STT).
    Возвращает распознанный текст, в котором найдено слово HOTWORD.
    Ничего не озвучивает, работает тихо.
    '''
    print(f"[hotword] waiting for: {HOTWORD!r}")
    while True:
        # короткая запись по VAD в отдельный файл
        record_wav_vad(AUDIO_HW_WAV)
        try:
            with open(AUDIO_HW_WAV, 'rb') as f:
                txt = client.audio.transcriptions.create(
                    model=STT_MODEL,
                    file=f,
                    response_format='text'
                ).strip()
        except Exception as e:
            print('[hotword] stt error:', e)
            txt = ''
        n = (txt or '').strip().lower().replace('ё','е')
        if HOTWORD in n:
            print(f"[hotword] detected: {txt!r}")
            return txt
        else:
            print(f"[hotword] miss: {txt!r}")
            time.sleep(0.2)
def append_dialog(user_text: str, assistant_text: str, meta: dict | None = None) -> None:
    rec = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "user": user_text,
        "assistant": assistant_text,
        "meta": meta or {},
    }
    with open(DIALOG_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def one_turn():
    # 0) Голосовой сигнал готовности (по-русски)
    try:
        print("[voice] Слушаю...")
        tmp_listen_mp3 = os.path.join(TEMP_DIR, "tts_listen.mp3")
        speech = client.audio.speech.create(
            model=TTS_MODEL,
            voice=TTS_VOICE,
            input="Слушаю"
        )
        with open(tmp_listen_mp3, "wb") as f:
            f.write(speech.read())
        play_mp3_mci(tmp_listen_mp3)
        time.sleep(0.15)
    except Exception as _e:
        print("[voice] skipped:", _e)

    # 1) Запись по VAD
    record_wav_vad(AUDIO_IN_WAV)

    # 2) STT
    print(f"[stt] model={STT_MODEL}")
    with open(AUDIO_IN_WAV, "rb") as f:
        stt = client.audio.transcriptions.create(
            model=STT_MODEL,
            file=f,
            response_format="text"
        )
    user_text = (stt or "").strip()
    print(f'[stt] text="{user_text}"')

    # 3) LLM (строго русские ответы; числа — словами)
    sysmsg = "Ty pomoshchnik Jarvis. Vsegda otvechai po-russki, nezavisimo ot yazyka zaprosa. Esli otvet - chislo, pishi ego slovami na russkom. Otvechai korotko i po delu."
    print(f"[llm] model={LLM_MODEL}")
    if not user_text:
        reply = "Я не расслышал запрос. Повторите, пожалуйста."
    else:
        chat = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": sysmsg},
                {"role": "user", "content": user_text},
            ],
            temperature=0.2,
            max_tokens=120,
        )
        reply = (chat.choices[0].message.content or "").strip()
    print(f'[llm] reply="{reply}"')

    # 4) TTS -> MP3
    print(f"[tts] model={TTS_MODEL}, voice={TTS_VOICE}")
    speech = client.audio.speech.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=reply,
    )
    with open(AUDIO_OUT_MP3, "wb") as f:
        f.write(speech.read())
    print(f"[tts] saved: {AUDIO_OUT_MP3}")

    # 5) Проигрывание
    print("[play] mp3 via MCI…")
    play_mp3_mci(AUDIO_OUT_MP3)

    # 6) Лог
    append_dialog(user_text=user_text, assistant_text=reply, meta={
        "stt_model": STT_MODEL,
        "llm_model": LLM_MODEL,
        "tts_model": TTS_MODEL,
        "voice": TTS_VOICE,
        "rate": SAMPLE_RATE,
        "vad": True,
    })
    print(f"[log] append -> {DIALOG_LOG}")
if __name__ == "__main__":
    print("=== Jarvis Voice Bridge v3 — Этап 3.2.3 / hotword ===")
    print(f"ROOT={ROOT}")
    print(f"LLM={LLM_MODEL} | STT={STT_MODEL} | TTS={TTS_MODEL}/{TTS_VOICE}")
    print(f"Горячее слово: '{HOTWORD}'. Скажи: 'Джарвис, ...'. Остановить — CTRL+C.")
    try:
        while True:
            hw_text = wait_hotword()         # ждём 'джарвис'
            # теперь стандартный цикл: голосовое 'Слушаю' → запись VAD → LLM → TTS
            one_turn()
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\\n[exit] Остановлено по CTRL+C")













