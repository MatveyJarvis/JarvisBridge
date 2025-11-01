# local_brain.py
# v2.1.2.3 — Чтение локальных правил из JSON

import os
import re
import json
from typing import Optional, List, Union

from dotenv import load_dotenv


def _normalize(text: str) -> str:
    t = (text or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t


class LocalBrain:
    """
    Загружает правила из JSON и даёт быстрый ответ без LLM.
    Поддерживаемые match:
      - "equals"        : точное совпадение строки
      - "contains_any"  : содержит ЛЮБОЕ из слов/фраз
      - "contains_all"  : содержит ВСЕ слова/фразы
      - "regex"         : регулярное выражение (осторожно)
    Структура JSON: {"rules":[{"match": "...", "pattern": ".../[]", "reply": "..."}]}
    """

    def __init__(self):
        load_dotenv()
        path = os.getenv("LOCAL_RULES_PATH", "config/local_rules.json")
        self.rules = self._load_rules(path)

    def _load_rules(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            rules = data.get("rules", [])
            return rules if isinstance(rules, list) else []
        except Exception:
            # Фолбэк: минимальный набор на случай отсутствия файла
            return [
                {"match": "equals", "pattern": "привет", "reply": "Привет! Я на связи."},
                {"match": "contains_any", "pattern": ["привет джарвис"], "reply": "Слушаю."},
            ]

    def try_answer(self, user_text: str) -> Optional[str]:
        nt = _normalize(user_text)
        for r in self.rules:
            mtype = str(r.get("match", "")).strip().lower()
            pattern = r.get("pattern")
            reply = r.get("reply")

            if not reply:
                continue

            if mtype == "equals":
                if nt == _normalize(str(pattern)):
                    return reply

            elif mtype == "contains_any":
                if isinstance(pattern, list):
                    for kw in pattern:
                        if _normalize(kw) in nt:
                            return reply
                else:
                    if _normalize(str(pattern)) in nt:
                        return reply

            elif mtype == "contains_all":
                if isinstance(pattern, list) and all(_normalize(kw) in nt for kw in pattern):
                    return reply

            elif mtype == "regex":
                try:
                    if re.search(str(pattern), nt):
                        return reply
                except Exception:
                    continue

        return None
