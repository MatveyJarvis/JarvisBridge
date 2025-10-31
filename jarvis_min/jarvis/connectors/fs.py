
from pathlib import Path
from typing import Iterator
from ..whitelist import Whitelist

class SafeFS:
    def __init__(self, wl: Whitelist):
        self.wl = wl

    def iter_files(self) -> Iterator[Path]:
        for base in self.wl.paths:
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if p.is_file() and self.wl.is_allowed_ext(p) and self.wl.is_allowed_size(p):
                    yield p
