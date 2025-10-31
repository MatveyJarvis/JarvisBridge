# -*- coding: utf-8 -*-
"""
utils/voice_logger.py
Надёжная запись JSONL в C:\JarvisBridge\logs\voice_dialog.jsonl
(создаёт папку автоматически, потокобезопасно)
"""

import os, io, json, datetime, threading

LOG_DIR  = r"C:\JarvisBridge\logs"
LOG_FILE = os.path.join(LOG_DIR, "voice_dialog.jsonl")
_lock = threading.Lock()

def _ensure_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

def log_turn(user_text: str, assistant_text: str, meta: dict = None):
    """
    Пишет одну строку JSONL
    """
    _ensure_dir()
    entry = {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "user": user_text or "",
        "assistant": assistant_text or "",
        "meta": meta or {}
    }
    line = json.dumps(entry, ensure_ascii=False)
    with _lock:
        with io.open(LOG_FILE, "a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")
