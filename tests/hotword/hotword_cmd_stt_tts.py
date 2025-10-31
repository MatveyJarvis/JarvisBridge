# -*- coding: utf-8 -*-
"""
hotword_cmd_stt_tts.py — A2.1 (robust wake)
- Поддержка списка WAKE_PHRASES из .env
- Фаззи-сравнение со всеми вариантами + ключевые слова ("джарвис", "jarvis")
- Порог совпадения снижен до 55%
- Остальное без изменений: после команды — TTS ("Команда получена: ...")
"""
import os, time, wave, difflib, re
from datetime import datetime
from pathlib import Path
import numpy as np
import sounddevice as sd
from openai import OpenAI
from dotenv import load_dotenv

ROOT = Path(r"C:\JarvisBridge")
TEMP = ROOT / "temp"
TEMP.mkdir(parents=True, exist_ok=True)
load_dotenv(ROOT / ".env", override=False)

def _normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s\-]", " ", s, flags=re.U)
    s = re.sub(r"\s+", " ", s, flags=re.U)
    return s

def _wake_variants() -> list[str]:
    env_list = os.getenv("WAKE_PHRASES", "")
    single   = os.getenv("WAKE_PHRASE", "")
    variants = []
    if env_list:
        variants += [ _normalize(p) for p in env_list.replace(",", ";").split(";") if p.strip() ]
    if single:
        variants.append(_normalize(single))
    if not variants:
        variants = ["привет джарвис", "джарвис привет", "привет jarvis", "jarvis привет", "привет", "джарвис", "jarvis"]
    # удаляем дубликаты, сохраняя порядок
    seen, out = set(), []
    for v in variants:
        if v and v not in seen:
            seen.add(v); out.append(v)
    return out

WAKE_LIST = _wake_variants()
INPUT_DEVICE_INDEX = int(os.getenv("INPUT_DEVICE_INDEX", "1"))
SR = int(os.getenv("INPUT_SAMPLE_RATE", "16000"))
CH = 1
STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
VOICE = os.getenv("OPENAI_TTS_VOICE", "alloy")
WAKE_OK_THRESHOLD = 55.0  # %

client = OpenAI()

def _save_wav(path, data):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CH); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((data * 32767).astype(np.int16).tobytes())

def _record(sec):
    frames = int(sec * SR)
    print(f"[rec] device={INPUT_DEVICE_INDEX}, dur={sec}s")
    data = sd.rec(frames, samplerate=SR, channels=CH, dtype="float32", device=INPUT_DEVICE_INDEX)
    sd.wait()
    return data.reshape(-1)

def _stt(path):
    with open(path, "rb") as f:
        r = client.audio.transcriptions.create(model=STT_MODEL, file=f, language="ru")
    return _normalize((r.text or ""))

def _sim(a,b): 
    return difflib.SequenceMatcher(None,a,b).ratio()*100

def _is_wake(text: str) -> tuple[bool, float, str]:
    # быстрый хак: ключевые слова
    if any(kw in text for kw in ["джарвис", "jarvis"]):
        return True, 100.0, "keyword"
    # берём лучшее совпадение по всем вариантам
    best_score, best_ref = 0.0, ""
    for ref in WAKE_LIST:
        score = _sim(text, ref)
        if score > best_score:
            best_score, best_ref = score, ref
    return (best_score >= WAKE_OK_THRESHOLD), best_score, best_ref

def _tts(text, out_path):
    print(f"[TTS] Озвучиваю: {text}")
    with client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL, voice=VOICE, input=text
    ) as resp:
        resp.stream_to_file(out_path)
    print(f"[TTS] Сохранено: {out_path}")
    os.system(f'start "" "{out_path}"')

def main():
    ts = int(time.time())
    for attempt in range(1,4):
        wake_path = TEMP / f"wake_try{attempt}_{ts}.wav"
        print(f"[Hotword] Попытка {attempt}/3. Скажи фразу (варианты): {', '.join(WAKE_LIST[:3])} ...")
        _save_wav(wake_path, _record(3.0))
        text = _stt(wake_path)
        ok, score, ref = _is_wake(text)
        print(f"[STT] Распознал: {text}  | best='{ref}' ({score:.1f}%)")
        if ok:
            print("[Hotword] ✅ Совпадение, говори команду…")
            cmd_path = TEMP / f"cmd_{ts}.wav"
            _save_wav(cmd_path, _record(6.0))
            cmd_text = _stt(cmd_path)
            print(f"[STT] Команда: {cmd_text}")
            tts_path = TEMP / f"tts_{ts}.mp3"
            _tts(f"Команда получена: {cmd_text}", tts_path)
            print("[Done]")
            return
        else:
            print("[Hotword] Не совпало, попробуем ещё раз.\n")
    print("[Hotword] ❌ Три неудачных попытки — выход.")

if __name__ == "__main__":
    sd.default.device = (None, INPUT_DEVICE_INDEX)
    main()
