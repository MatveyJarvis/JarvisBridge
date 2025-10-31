# -*- coding: utf-8 -*-
"""
hotword_cmd_stt_llm_tts.py — A3.3
- FIX: убран неподдерживаемый аргумент format у speech.create (SDK-совместимость)
- TTS пишем в MP3 и проигрываем минимизировано (start /min), чтобы не мешало
- Озвучка "Слушаю" при пробуждении
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

def _normalize(s):
    s = s.lower().strip()
    s = re.sub(r"[^\w\s\-]", " ", s, flags=re.U)
    s = re.sub(r"\s+", " ", s, flags=re.U)
    return s

def _wake_variants():
    env_list = os.getenv("WAKE_PHRASES", "")
    single   = os.getenv("WAKE_PHRASE", "")
    variants = []
    if env_list:
        variants += [ _normalize(p) for p in env_list.replace(",", ";").split(";") if p.strip() ]
    if single:
        variants.append(_normalize(single))
    if not variants:
        variants = ["привет джарвис", "джарвис", "jarvis"]
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
LLM_MODEL = os.getenv("OPENAI_LLM_MODEL_STRONG", "gpt-4o")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
VOICE     = os.getenv("OPENAI_TTS_VOICE", "alloy")
THR = 55.0

ACK_ON_WAKE = True  # озвучивать "Слушаю" при срабатывании пробуждения

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

def _is_wake(text):
    if any(k in text for k in ["джарвис", "jarvis"]):
        return True, 100.0, "keyword"
    best, ref = 0.0, ""
    for p in WAKE_LIST:
        s = _sim(text,p)
        if s>best: best,ref=s,p
    return best>=THR, best, ref

def _tts_to_mp3_and_play_min(text: str, out_path: Path):
    print(f"[TTS] Озвучиваю: {text}")
    # В твоей версии SDK параметр format не поддерживается — пишем в mp3 по умолчанию
    with client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=VOICE,
        input=text
    ) as resp:
        resp.stream_to_file(str(out_path))
    # Проигрываем минимизировано, чтобы окно не мешало
    os.system(f'start /min "" "{out_path}"')

def _llm_answer(prompt:str) -> str:
    try:
        r = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role":"system","content":"Ты голосовой помощник Джарвис. Отвечай кратко и по делу, на русском."},
                {"role":"user","content":prompt}
            ],
            temperature=float(os.getenv("OPENAI_TEMPERATURE","0.4"))
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка при обращении к модели: {e}"

def main():
    ts = int(time.time())
    for attempt in range(1,4):
        wake_path = TEMP / f"wake_try{attempt}_{ts}.wav"
        print(f"[Hotword] Попытка {attempt}/3. Скажи фразу (варианты): {', '.join(WAKE_LIST[:3])} ...")
        _save_wav(wake_path, _record(3.0))
        text = _stt(wake_path)
        ok, score, ref = _is_wake(text)
        print(f"[STT] Распознал: {text} | best='{ref}' ({score:.1f}%)")
        if ok:
            print("[Hotword] ✅ Совпадение, говори команду…")
            if ACK_ON_WAKE:
                _tts_to_mp3_and_play_min("Слушаю", TEMP / f"tts_ack_{ts}.mp3")

            cmd_path = TEMP / f"cmd_{ts}.wav"
            _save_wav(cmd_path, _record(6.0))
            cmd_text = _stt(cmd_path)
            print(f"[STT] Команда: {cmd_text}")

            answer = _llm_answer(cmd_text)
            print(f"[LLM] Ответ: {answer}")

            _tts_to_mp3_and_play_min(answer, TEMP / f"tts_{ts}.mp3")
            print("[Done]")
            return
        else:
            print("[Hotword] Не совпало, попробуем ещё раз.\n")
    print("[Hotword] ❌ Три неудачных попытки — выход.")

if __name__ == "__main__":
    sd.default.device = (None, INPUT_DEVICE_INDEX)
    main()
