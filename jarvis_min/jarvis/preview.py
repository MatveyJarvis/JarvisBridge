from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
import csv

# --- Вспомогательные функции ---
def _read_text(path: Path, max_bytes: int = 2_000_000) -> str:
    """
    Читает текстовый файл с попыткой авто-энкодинга (utf-8, cp1251).
    Ограничение: не больше max_bytes.
    """
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"Файл слишком большой для предпросмотра: {size} байт (> {max_bytes}).")

    encodings = ("utf-8-sig", "utf-8", "cp1251")
    last_err = None
    for enc in encodings:
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception as e:
            last_err = e
    raise last_err or RuntimeError("Не удалось прочитать файл")
