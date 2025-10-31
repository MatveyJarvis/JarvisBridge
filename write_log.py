# -*- coding: utf-8 -*-
"""
write_log.py — отдельный безопасный логгер
Вызывается из основного скрипта через os.system(...)
"""
import sys, os, json
from datetime import datetime

BASE_DIR = r"C:\JarvisBridge"
LOGS_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOGS_DIR, "voice_dialog.jsonl")

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def main():
    try:
        user = sys.argv[1] if len(sys.argv) > 1 else ""
        jarvis = sys.argv[2] if len(sys.argv) > 2 else ""
        ensure_dir(LOGS_DIR)
        rec = {"timestamp": now(), "user": user, "jarvis": jarvis}
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"[LOGGER] {rec['timestamp']} | {user} -> {jarvis}")
    except Exception as e:
        print(f"[LOGGER][ERROR] {e}")

if __name__ == "__main__":
    main()
