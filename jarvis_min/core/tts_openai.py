# tts_openai.py
# ─────────────────────────────────────────────────────────────────────────────
# TTS через OpenAI (REST) + воспроизведение через ffplay из stdin (без временных файлов).
# Сам ищет OPENAI_API_KEY: сначала в окружении, затем в .env (в текущей или родительских папках).
#
# Требования:
#   - pip install requests
#   - установленный FFmpeg (ffplay.exe должен быть в PATH)
#
# Пример:
#   import tts_openai as t
#   t.say("Привет! Проверка голоса.")
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import os
import sys
import json
import subprocess
from typing import Tuple, Optional

import requests


# ─────────────────────────────────────────────────────────────────────────────
# Утилиты: ffplay и .env
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_ffplay_available() -> None:
    """Проверяем доступность ffplay в PATH."""
    try:
        subprocess.run(
            ["ffplay", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "ffplay не найден. Установите FFmpeg и добавьте "
            r"C:\Program Files\FFmpeg\bin в PATH."
        )


def _find_env_path(start: Optional[str] = None) -> Optional[str]:
    """Ищет .env в текущей и родительских папках."""
    cur = os.path.abspath(start or os.getcwd())
    root = os.path.abspath(os.path.splitdrive(cur)[0] + os.sep)
    while True:
        env_path = os.path.join(cur, ".env")
        if os.path.isfile(env_path):
            return env_path
        if cur == root:
            return None
        cur = os.path.dirname(cur)


def _load_env_file_to_environ(env_path: str) -> None:
    """Простой парсер .env: KEY=VALUE, строки с # игнорируются."""
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(env_path, "r", encoding="cp1251") as f:
            lines = f.readlines()
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        key, val = s.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def _get_api_key() -> str:
    """Возвращает OPENAI_API_KEY. Ищет в окружении, затем подгружает из .env."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        return api_key

    env_path = _find_env_path()
    if env_path:
        _load_env_file_to_environ(env_path)
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if api_key:
            return api_key

    raise RuntimeError(
        "OPENAI_API_KEY не найден. Установите переменную окружения или добавьте в .env строку:\n"
        "OPENAI_API_KEY=sk-...  (не делитесь ключом!)"
    )


def _detect_mime_from_bytes(data: bytes, default: str = "audio/mpeg") -> str:
    """Очень грубое определение типа аудио по сигнатуре."""
    if not data:
        return default
    if data[:4] == b"RIFF":
        return "audio/wav"
    if data[:3] == b"ID3" or data[:2] in (b"\xFF\xFB", b"\xFF\xF3"):
        return "audio/mpeg"
    return default


def _play_via_ffplay_stdin(audio_bytes: bytes) -> None:
    """Проигрывает аудиобайты через ffplay по stdin (без записи на диск)."""
    if not audio_bytes:
        print("Нет данных для воспроизведения", file=sys.stderr)
        return

    _ensure_ffplay_available()

    try:
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-"],
            input=audio_bytes,
            check=False,
        )
    except Exception as e:
        print(f"Ошибка воспроизведения через ffplay: {e}", file=sys.stderr)


# ─────────────────────────────────────────────────────────────────────────────
# Запрос к OpenAI TTS (REST)
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_tts_bytes_via_rest(
    text: str,
    *,
    model: str = "gpt-4o-mini-tts",
    voice: str = "alloy",
    out_format: str = "mp3",
) -> Tuple[bytes, str]:
    """
    Получает синтезированное аудио из OpenAI (REST).
    Возвращает (audio_bytes, mime).
    """
    api_key = _get_api_key()
    project_id = os.getenv("OPENAI_PROJECT_ID", "").strip()  # опционально

    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if project_id:
        headers["OpenAI-Project"] = project_id  # безопасно: если нет — игнорируется сервером

    payload = {
        "model": model,
        "voice": voice,
        "input": text,
        "format": out_format,  # mp3 или wav
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI TTS ошибка {resp.status_code}: {resp.text[:500]}")

    data = resp.content or b""
    mime = resp.headers.get("Content-Type") or _detect_mime_from_bytes(data)
    if not data:
        raise RuntimeError("Пустой ответ аудио от OpenAI.")

    return data, mime


# ─────────────────────────────────────────────────────────────────────────────
# Публичный API
# ─────────────────────────────────────────────────────────────────────────────

def synthesize(
    text: str,
    *,
    model: str = "gpt-4o-mini-tts",
    voice: str = "alloy",
    out_format: str = "mp3",
) -> Tuple[bytes, str]:
    """Синтезирует речь и возвращает (audio_bytes, mime)."""
    if not text or not text.strip():
        raise ValueError("Пустой текст для синтеза речи.")
    return _fetch_tts_bytes_via_rest(text, model=model, voice=voice, out_format=out_format)


def say(
    text: str,
    *,
    model: str = "gpt-4o-mini-tts",
    voice: str = "alloy",
    out_format: str = "mp3",
    autoplay: bool = True,
) -> bytes:
    """
    Синтезирует речь и, если autoplay=True, воспроизводит её.
    Возвращает сырые байты аудио.
    """
    audio_bytes, _ = synthesize(text, model=model, voice=voice, out_format=out_format)
    if autoplay:
        _play_via_ffplay_stdin(audio_bytes)
    return audio_bytes


# ─────────────────────────────────────────────────────────────────────────────
# Запуск из консоли:
#   python -m tts_openai "Текст для проверки"
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    phrase = " ".join(sys.argv[1:]).strip() or "Привет! Проверка нейронного голоса OpenAI."
    say(phrase)
