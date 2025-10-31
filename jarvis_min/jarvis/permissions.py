
# Каркас для уровней доверия и самообучения (Level 3)
from dataclasses import dataclass
from typing import Literal

TrustLevel = Literal["low", "medium", "high"]

@dataclass
class PermissionContext:
    trust: TrustLevel = "low"
    dry_run: bool = True  # по умолчанию режим сухого прогона
    user_id: str | None = None

    def allow_fs_write(self) -> bool:
        return self.trust in ("medium", "high") and not self.dry_run

    def allow_network(self) -> bool:
        return self.trust == "high" and not self.dry_run
