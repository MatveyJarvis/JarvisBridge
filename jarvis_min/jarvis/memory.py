from __future__ import annotations
from pathlib import Path
from datetime import datetime
import json
from typing import Any

DEFAULT_PATH = Path("data") / "memory.jsonl"

def _ts() -> str:
    return datetime.now().isoformat(timespec="seconds")

def append_event(event: dict[str, Any], path: Path = DEFAULT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _ts(), **event}, ensure_ascii=False) + "\n")
    return path

def tail(n: int = 20, path: Path = DEFAULT_PATH) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()[-n:]]
