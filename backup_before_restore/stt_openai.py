# stt_openai.py — REST + whisper-1 (устойчивый STT с явным language='ru')
import os, pathlib, requests
from dotenv import load_dotenv

BASE = pathlib.Path(__file__).resolve().parent
TEMP = BASE / "temp"
TEMP.mkdir(exist_ok=True)

TRANSCRIBE_URL = "https://api.openai.com/v1/audio/transcriptions"

def _get_key():
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("[STT] OPENAI_API_KEY пуст. Заполни .env")
    return key

def transcribe(audio_path: str, language: str = "ru", model: str = None) -> str:
    """
    Распознаёт локальный аудиофайл (wav/mp3/ogg/…).
    По умолчанию язык — русский. Возвращает текст (может быть пустым).
    """
    key = _get_key()
    model = (model or os.getenv("OPENAI_STT_MODEL") or "whisper-1").strip()

    headers = {"Authorization": f"Bearer {key}"}
    data = {
        "model": model,
        "language": language or "ru",
        "response_format": "verbose_json"
    }
    with open(audio_path, "rb") as f:
        files = {"file": (pathlib.Path(audio_path).name, f, "application/octet-stream")}
        r = requests.post(TRANSCRIBE_URL, headers=headers, data=data, files=files, timeout=120)
        r.raise_for_status()
        js = r.json()
        return (js.get("text") or "").strip()
