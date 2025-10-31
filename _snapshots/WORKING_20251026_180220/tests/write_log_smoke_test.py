# -*- coding: utf-8 -*-
"""
write_log_smoke_test.py
Создаёт C:\JarvisBridge\logs\voice_dialog.jsonl и записывает одну строку JSON.
"""

import os, json, datetime, io

LOG_DIR  = r"C:\JarvisBridge\logs"
LOG_FILE = os.path.join(LOG_DIR, "voice_dialog.jsonl")

def ensure_dir(p):
    if not os.path.exists(p):
        os.makedirs(p, exist_ok=True)

def append_jsonl(path, obj):
    with io.open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

ensure_dir(LOG_DIR)
entry = {
    "ts": datetime.datetime.now().isoformat(timespec="seconds"),
    "user": "привет джарвис, 2 плюс 2",
    "assistant": "4",
    "meta": {"test": True}
}
append_jsonl(LOG_FILE, entry)
print(f"[✓] Записано в {LOG_FILE}")
