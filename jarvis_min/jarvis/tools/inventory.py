from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Iterable
import csv
from ..connectors.fs import SafeFS

@dataclass
class FileRow:
    path: str
    name: str
    ext: str
    size_mb: float
    mtime_iso: str

def build_inventory(fs: SafeFS) -> Iterable[FileRow]:
    from datetime import datetime
    for p in fs.iter_files():
        st = p.stat()
        yield FileRow(
            path=str(p),
            name=p.name,
            ext=p.suffix.lower(),
            size_mb=round(st.st_size / (1024 * 1024), 3),
            mtime_iso=datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        )

def write_csv(rows: Iterable[FileRow], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    headers = ["path", "name", "ext", "size_mb", "mtime_iso"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))
    return out_path
