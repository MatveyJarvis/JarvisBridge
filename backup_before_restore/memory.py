# memory.py
# v2.1.6 — простая контекстная память последних N реплик

import os, json
from typing import List, Dict, Any
from dotenv import load_dotenv

class Memory:
    def __init__(self):
        load_dotenv()
        self.enabled = os.getenv("MEMORY_ENABLED", "1").strip() != "0"
        self.path = os.getenv("MEMORY_PATH", "temp\\memory.json")
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
        except Exception:
            pass
        self.max_turns = max(1, min(20, int(os.getenv("MEMORY_TURNS", "6"))))

    def load(self) -> List[Dict[str, str]]:
        if not self.enabled:
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data[-self.max_turns:]
        except Exception:
            pass
        return []

    def save(self, history: List[Dict[str, str]]):
        if not self.enabled:
            return
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(history[-self.max_turns:], f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add(self, role: str, content: str):
        if not self.enabled:
            return
        hist = self.load()
        hist.append({"role": role, "content": content})
        self.save(hist)

    def clear(self):
        try:
            if os.path.exists(self.path):
                os.remove(self.path)
        except Exception:
            pass
