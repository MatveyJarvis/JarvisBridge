# jarvis_hotword_vad.py
# Always-on Jarvis: Wake-Word + улучшенный VAD (webrtcvad если есть, иначе energy) + OS-Bridge.
# Зависимости:
#   pip install -U openai python-dotenv sounddevice pydub
#   (опционально) pip install webrtcvad
# Нужен ffmpeg в PATH. Проигрывание — winsound (Windows).

import os, io, time, json, wave, math, collections, re
from dataclasses import dataclass
from typing import List, Tuple, Optional

import sounddevice as sd
from pydub import AudioSegment
from dotenv import load_dotenv
from openai import OpenAI, __version__ as openai_version
import winsound

# --- webrtcvad (если есть) ---
USE_WEBRTCVAD = True
try:
    import webrtcvad  # type: ignore
except Exception:
    USE_WEBRTCVAD = False

# === OS Bridge (локальные действия) ===
import os_bridge  # файл os_bridge.py рядом


# ---------------- Config ----------------
def load_config():
    load_dotenv()
    cfg = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "").strip(),
        "OPENAI_PROJECT_ID": os.getenv("OPENAI_PROJECT_ID", "").strip(),

        "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
        "STT_MODEL": os.getenv("STT_MODEL", "gpt-4o-mini-transcribe").strip(),
        "TTS_MODEL": os.getenv("TTS_MODEL", "gpt-4o-mini-tts").strip(),
        "TTS_VOICE": os.getenv("TTS_VOICE", "alloy").strip(),

        "SYSTEM_PROMPT": os.getenv("SYSTEM_PROMPT", (
            "Ты Jarvis. Отвечай кратко и по делу. "
            "Если нужно выполнить локальное действие в Windows, дополни ответ строкой:\n"
            "OS: {\"action\":\"open_app|open_path|create_dir|list_dir|search_files\","
            "\"target\":\"...\", \"args\":{}}\n"
            "Сначала скажи человеку, что будешь делать, затем отдельно строку OS: {...}."
        )).strip(),

        # Wake word + VAD
        "WAKE_WORD_ENABLED": os.getenv("WAKE_WORD_ENABLED", "true").lower() == "true",
        "WAKE_WORDS": [w.strip() for w in os.getenv(
            "WAKE_WORDS", "привет джарвис|эй джарвис|hey jarvis|ok jarvis"
        ).lower().split("|") if w.strip()],

        # VAD настройки
        "VAD_FRAME_MS": int(os.getenv("VAD_FRAME_MS", "20")),          # 10/20/30 (под webrtcvad)
        "VAD_MAX_SILENCE_MS": int(os.getenv("VAD_MAX_SILENCE_MS", "1200")),
        "VAD_AGGRESSIVENESS": int(os.getenv("VAD_AGGRESSIVENESS", "2")),  # 0..3 для webrtcvad
        "VAD_PREROLL_MS": int(os.getenv("VAD_PREROLL_MS", "200")),
        "VAD_POSTROLL_MS": int(os.getenv("VAD_POSTROLL_MS", "300")),

        # Audio (жёстко под STT): 16k/mono/16bit
        "SAMPLE_RATE": 16000,
        "CHANNELS": 1,

        # UX
        "GREETING_ON_START": os.getenv("GREETING_ON_START", "true").lower() == "true",
        "GREETING_TEXT": os.getenv("GREETING_TEXT", "Готов к работе").strip(),
        "LISTENING_BEEP": os.getenv("LISTENING_BEEP", "true").lower() == "true",

        # Язык для STT
        "STT_LANGUAGE": os.getenv("STT_LANGUAGE", "ru").strip(),
    }
    if not cfg["OPENAI_API_KEY"]:
        raise RuntimeError("OPENAI_API_KEY пуст в .env")
    return cfg


def build_openai_client(cfg):
    kwargs = {"api_key": cfg["OPENAI_API_KEY"]}
    if cfg["OPENAI_API_KEY"].startswith("sk-proj-") and cfg["OPENAI_PROJECT_ID"]:
        kwargs["project"] = cfg["OPENAI_PROJECT_ID"]
    return OpenAI(**kwargs)


# ----------- Audio helpers (TTS) -----------
def play_wav(wav_path: str):
    winsound.PlaySound(wav_path, winsound.SND_FILENAME)
    try: os.remove(wav_path)
    except: pass

def bytes_to_wav_in_project(mp3_or_wav_bytes: bytes, name="tts_out") -> str:
    try:
        seg = AudioSegment.from_file(io.BytesIO(mp3_or_wav_bytes), format="mp3")
    except Exception:
        seg = AudioSegment.from_file(io.BytesIO(mp3_or_wav_bytes), format="wav")
    wav_path = os.path.join(os.getcwd(), f"{name}.wav")
    seg.export(wav_path, format="wav", parameters=["-acodec", "pcm_s16le"])
    return wav_path

def tts_say(client: OpenAI, cfg, text: str):
    if not text: return
    mp3_path = os.path.join(os.getcwd(), "tts_out.mp3")
    # streaming
    try:
        with client.audio.speech.with_streaming_response.create(
            model=cfg["TTS_MODEL"], voice=cfg["TTS_VOICE"], input=text
        ) as resp:
            resp.stream_to_file(mp3_path)
        with open(mp3_path, "rb") as f: mp3 = f.read()
        wav = bytes_to_wav_in_project(mp3)
        play_wav(wav)
        try: os.remove(mp3_path)
        except: pass
        return
    except Exception:
        pass
    # fallback
    speech = client.audio.speech.create(model=cfg["TTS_MODEL"], voice=cfg["TTS_VOICE"], input=text)
    audio_bytes = speech.read()
    wav = bytes_to_wav_in_project(audio_bytes)
    play_wav(wav)


# ----------- VAD recorder (ring buffer) -----------
@dataclass
class VadConfig:
    samplerate: int = 16000
    frame_ms: int = 20
    max_silence_ms: int = 1200
    aggressiveness: int = 2
    preroll_ms: int = 200
    postroll_ms: int = 300

def _rms_int16(pcm: bytes) -> float:
    n = len(pcm) // 2
    if n == 0: return 0.0
    s = 0
    for i in range(0, len(pcm), 2):
        v = int.from_bytes(pcm[i:i+2], "little", signed=True)
        s += v * v
    return math.sqrt(s / n)

def record_utterance_vad(vad_cfg: VadConfig) -> bytes:
    """
    Запись высказывания с пред/пост-буфером:
    - RawInputStream 16k/mono/16bit
    - ring-buffer на preroll/postroll
    - старт по речи, стоп по тишине max_silence_ms
    - формируем корректный WAV
    """
    bytes_per_frame = int(vad_cfg.samplerate * vad_cfg.frame_ms / 1000) * 2  # 16-bit mono
    pre_frames = max(1, vad_cfg.preroll_ms // vad_cfg.frame_ms)
    post_frames = max(1, vad_cfg.postroll_ms // vad_cfg.frame_ms)
    ring = collections.deque(maxlen=pre_frames)

    vad = webrtcvad.Vad(vad_cfg.aggressiveness) if USE_WEBRTCVAD else None

    frames: List[bytes] = []
    silence_ms = 0
    speaking = False

    with sd.RawInputStream(samplerate=vad_cfg.samplerate, channels=1, dtype="int16") as stream:
        # Калибровка для energy-VAD
        noise_vals = []
        for _ in range(max(1, int(400 / vad_cfg.frame_ms))):
            buf = stream.read(bytes_per_frame)[0]
            noise_vals.append(_rms_int16(buf))
        noise_floor = (sum(noise_vals) / len(noise_vals)) if noise_vals else 200.0
        start_thr = max(250.0, noise_floor * 1.5)
        stop_thr  = max(180.0, noise_floor * 1.2)

        # Основной цикл
        while True:
            buf = stream.read(bytes_per_frame)[0]
            ring.append(buf)

            if vad:
                is_speech = vad.is_speech(buf, vad_cfg.samplerate)
            else:
                is_speech = _rms_int16(buf) > (start_thr if not speaking else stop_thr)

            if not speaking:
                if is_speech:
                    speaking = True
                    # добавляем предисторию
                    frames.extend(list(ring))
                    frames.append(buf)
                    silence_ms = 0
            else:
                frames.append(buf)
                if is_speech:
                    silence_ms = 0
                else:
                    silence_ms += vad_cfg.frame_ms
                    if silence_ms >= vad_cfg.max_silence_ms:
                        for _ in range(post_frames):
                            frames.append(stream.read(bytes_per_frame)[0])
                        break

    # Собираем валидный WAV
    raw_pcm = b"".join(frames)
    bio = io.BytesIO()
    with wave.open(bio, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(vad_cfg.samplerate)
        w.writeframes(raw_pcm)
    return bio.getvalue()


# ----------- STT / LLM -----------
def transcribe_bytes(client: OpenAI, cfg, wav_bytes: bytes) -> str:
    tmp = os.path.join(os.getcwd(), "hotword_input.wav")
    with open(tmp, "wb") as f:
        f.write(wav_bytes)
    try:
        with open(tmp, "rb") as f:
            resp = client.audio.transcriptions.create(
                model=cfg["STT_MODEL"],
                file=f,
                language=cfg["STT_LANGUAGE"] or "ru"
            )
        return getattr(resp, "text", "").strip()
    finally:
        try: os.remove(tmp)
        except: pass

def chat(client: OpenAI, cfg, user_text: str) -> str:
    resp = client.chat.completions.create(
        model=cfg["OPENAI_MODEL"],
        messages=[
            {"role": "system", "content": cfg["SYSTEM_PROMPT"]},
            {"role": "user", "content": user_text}
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


# ----------- Wake Word -----------
def _normalize(text: str) -> str:
    # нижний регистр, ё→е, убираем всё кроме букв/цифр/пробелов, схлопываем пробелы
    t = text.lower().replace("ё", "е")
    t = re.sub(r"[^a-zа-я0-9 ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def contains_wake_word(text: str, wake_words: List[str]) -> bool:
    t = _normalize(text)
    # нормализуем и словарь триггеров
    words_norm = [_normalize(w) for w in wake_words]
    return any(w in t for w in words_norm)


# ----------- OS-Bridge hook -----------
def maybe_execute_os_bridge(assistant_text: str) -> Tuple[str, Optional[str]]:
    os_line = None
    for line in assistant_text.splitlines():
        if line.strip().startswith("OS:"):
            os_line = line.strip()[3:].strip()
            break
    report = None
    if os_line:
        try:
            payload = json.loads(os_line)
            report = os_bridge.execute(payload)
            assistant_text = "\n".join(
                l for l in assistant_text.splitlines() if not l.strip().startswith("OS:")
            ).strip()
        except Exception as e:
            report = f"OS-Bridge: ошибка разбора команды: {e}"
    return assistant_text, report


# ----------- Main -----------
def main():
    cfg = load_config()
    client = build_openai_client(cfg)

    print(rf"""
┌──────────────────────────────────────────────────────────┐
│   Jarvis Hotword + VAD ({'webrtcvad' if USE_WEBRTCVAD else 'energy'}) + OS-Bridge   │
│         Скажи: "Привет, Джарвис" / "Hey Jarvis"          │
└──────────────────────────────────────────────────────────┘
""")
    print(f"OpenAI SDK: {openai_version}")
    print(f"LLM: {cfg['OPENAI_MODEL']} | STT: {cfg['STT_MODEL']} | TTS: {cfg['TTS_MODEL']}({cfg['TTS_VOICE']})")
    print(f"VAD: {'webrtcvad' if USE_WEBRTCVAD else 'energy'} (frame={cfg['VAD_FRAME_MS']} ms, "
          f"max_silence={cfg['VAD_MAX_SILENCE_MS']} ms, pre={cfg['VAD_PREROLL_MS']} ms, post={cfg['VAD_POSTROLL_MS']} ms)\n")

    if cfg["GREETING_ON_START"]:
        try: tts_say(client, cfg, cfg["GREETING_TEXT"])
        except Exception as e: print("Ошибка приветствия:", e)

    vad_cfg = VadConfig(
        samplerate=cfg["SAMPLE_RATE"],
        frame_ms=cfg["VAD_FRAME_MS"],
        max_silence_ms=cfg["VAD_MAX_SILENCE_MS"],
        aggressiveness=cfg["VAD_AGGRESSIVENESS"],
        preroll_ms=cfg["VAD_PREROLL_MS"],
        postroll_ms=cfg["VAD_POSTROLL_MS"],
    )

    while True:
        print("⏳ Жду wake-word… (Ctrl+C — выход)")
        wav = record_utterance_vad(vad_cfg)
        text = transcribe_bytes(client, cfg, wav)
        if not text:
            continue
        print(f"👂 Услышал: {text}")

        if cfg["WAKE_WORD_ENABLED"] and not contains_wake_word(text, cfg["WAKE_WORDS"]):
            continue

        if cfg["LISTENING_BEEP"]:
            winsound.MessageBeep()
        try: tts_say(client, cfg, "Слушаю")
        except Exception: pass

        cmd_wav = record_utterance_vad(vad_cfg)
        user_text = transcribe_bytes(client, cfg, cmd_wav)
        if not user_text:
            tts_say(client, cfg, "Не расслышал команду.")
            continue

        print(f"🧑 Ты: {user_text}")
        print("🤖 Думаю…")
        assistant = chat(client, cfg, user_text)
        assistant, os_report = maybe_execute_os_bridge(assistant)
        print(f"🤖 Jarvis: {assistant}")
        if os_report:
            print(f"🖥  {os_report}")
            assistant += f"\n{os_report}"

        try: tts_say(client, cfg, assistant)
        except Exception as e: print("Ошибка TTS:", e)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nВыход.")
