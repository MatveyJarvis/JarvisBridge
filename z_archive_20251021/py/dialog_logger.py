# dialog_logger.py
# v2.1.7 — JSONL-журнал диалогов

import os, json, uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

class DialogLogger:
    def __init__(self):
        load_dotenv()
        self.enabled = os.getenv("DIALOG_LOG_ENABLED", "1").strip() != "0"
        self.path = os.getenv("DIALOG_LOG_PATH", "logs\\dialog.jsonl")
        ttl_min = int(os.getenv("DIALOG_SESSION_TTL_MIN", "120"))
        self.ttl = timedelta(minutes=max(5, ttl_min))
        self._session_id = None
        self._last_ts = None
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
        except Exception:
            pass

    def _session(self):
        now = datetime.utcnow()
        if not self._session_id or not self._last_ts or (now - self._last_ts) > self.ttl:
            self._session_id = uuid.uuid4().hex[:12]
        self._last_ts = now
        return self._session_id

    def log(self, role: str, text: str, meta: dict = None):
        if not self.enabled:
            return
        rec = {
            "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "session": self._session(),
            "role": role,
            "text": text,
            "meta": meta or {}
        }
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass
