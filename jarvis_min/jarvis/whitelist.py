
from pathlib import Path
import yaml
from typing import Iterable

class Whitelist:
    def __init__(self, yaml_path: str):
        self.yaml_path = Path(yaml_path)
        self.paths: list[Path] = []
        self.extensions: set[str] = set()
        self.max_file_mb: int = 50
        self._load()

    def _load(self):
        data = {}
        if self.yaml_path.exists():
            data = yaml.safe_load(self.yaml_path.read_text(encoding="utf-8")) or {}
        for p in data.get("paths", []):
            self.paths.append(Path(p))
        for ext in data.get("extensions", []):
            self.extensions.add(ext.lower())
        self.max_file_mb = int(data.get("max_file_mb", 50))

    def is_allowed_path(self, p: Path) -> bool:
        p = p.resolve()
        return any(str(p).lower().startswith(str(base.resolve()).lower()) for base in self.paths)

    def is_allowed_ext(self, p: Path) -> bool:
        return p.suffix.lower() in self.extensions

    def is_allowed_size(self, p: Path) -> bool:
        try:
            size_mb = p.stat().st_size / (1024*1024)
        except FileNotFoundError:
            return False
        return size_mb <= self.max_file_mb
