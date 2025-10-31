# -*- coding: utf-8 -*-
"""
state_control.py
Хранение и смена состояния Jarvis: idle | active | paused
Файл: C:\JarvisBridge\temp\state.json
"""

import os, json, threading

BASE_DIR  = r"C:\JarvisBridge"   # raw-string → без предупреждений
TEMP_DIR  = os.path.join(BASE_DIR, "temp")
STATE_PATH= os.path.join(TEMP_DIR, "state.json")
_lock = threading.Lock()

DEFAULT_STATE = {"state": "idle"}  # при старте ждём активации

def _ensure_dir():
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR, exist_ok=True)

def _read_state():
    if not os.path.exists(STATE_PATH):
        return DEFAULT_STATE.copy()
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_STATE.copy()

def _write_state(obj):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)

def set_state(new_state: str):
    assert new_state in ("idle", "active", "paused")
    _ensure_dir()
    with _lock:
        _write_state({"state": new_state})

def get_state() -> str:
    _ensure_dir()
    with _lock:
        return _read_state().get("state", "idle")
