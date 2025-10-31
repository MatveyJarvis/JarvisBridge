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

    encodings = ("utf-8", "cp1251", "utf-8-sig")
    last_err = None
    for enc in encodings:
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception as e:
            last_err = e
    raise last_err or RuntimeError("Не удалось прочитать файл")

# --- Публичные функции предпросмотра ---

def head_text(path: Path, n_lines: int = 20) -> List[str]:
    """
    Возвращает первые n_lines строк текстового файла.
    """
    content = _read_text(path)
    lines = content.splitlines()
    return lines[: max(0, n_lines)]

def head_csv(path: Path, n_rows: int = 20) -> Tuple[List[str], List[List[str]]]:
    """
    Возвращает заголовки CSV (если есть) и первые n_rows строк (списки ячеек).
    Предполагаем разделитель по умолчанию ';' или ',' — автоопределение через Sniffer.
    """
    raw = _read_text(path)
    sample = raw[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
    except Exception:
        dialect = csv.excel
        dialect.delimiter = ";"

    reader = csv.reader(raw.splitlines(), dialect=dialect)
    rows = list(reader)

    headers: List[str] = []
    data: List[List[str]] = rows
    # если первая строка похожа на заголовки
    try:
        if rows and csv.Sniffer().has_header(sample):
            headers = rows[0]
            data = rows[1:]
    except Exception:
        pass

    return headers, data[: max(0, n_rows)]
