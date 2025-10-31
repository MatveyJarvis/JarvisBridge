# hud.py
# v2.1.3.2b — HUD с авто-бэкендом: winotify → win10toast → тихий фолбэк

import os
from typing import Optional
from dotenv import load_dotenv

# Кэш выбранного бэкенда
_BACKEND = None  # "winotify" | "win10toast" | "none"
_TOASTER = None  # объект бэкенда

def _pick_backend():
    global _BACKEND, _TOASTER
    if _BACKEND is not None:
        return _BACKEND

    load_dotenv()
    prefer = os.getenv("HUD_BACKEND", "auto").strip().lower()  # auto|winotify|win10toast|none

    # 1) Пытаемся winotify
    if prefer in ("auto", "winotify"):
        try:
            from winotify import Notification, audio  # noqa: F401
            _BACKEND = "winotify"
            _TOASTER = "winotify"
            return _BACKEND
        except Exception:
            if prefer == "winotify":
                _BACKEND = "none"
                return _BACKEND

    # 2) Пытаемся win10toast
    if prefer in ("auto", "win10toast"):
        try:
            from win10toast import ToastNotifier  # noqa: F401
            _BACKEND = "win10toast"
            _TOASTER = ToastNotifier()
            return _BACKEND
        except Exception:
            if prefer == "win10toast":
                _BACKEND = "none"
                return _BACKEND

    _BACKEND = "none"
    return _BACKEND


def notify(title: str, message: str, duration: int = 4) -> bool:
    """
    Показать тост-уведомление. Возвращает True/False.
    Управление через .env:
      HUD_ENABLED=1|0
      HUD_BACKEND=auto|winotify|win10toast|none
      HUD_ICON=путь_к_ico
      HUD_DURATION=секунды
    """
    load_dotenv()
    if os.getenv("HUD_ENABLED", "1").strip() == "0":
        return False

    backend = _pick_backend()
    if backend == "none":
        return False

    # Обрежем слишком длинные сообщения
    msg = (message or "").strip()
    if len(msg) > 200:
        msg = msg[:197] + "..."

    icon = os.getenv("HUD_ICON", "").strip()
    icon_path = icon if (icon and os.path.exists(icon)) else None
    try:
        dur = max(2, int(os.getenv("HUD_DURATION", str(duration))))
    except Exception:
        dur = max(2, duration)

    try:
        if backend == "winotify":
            # Уведомления Win10/11 (стабильно на Win11)
            from winotify import Notification, audio
            toast = Notification(app_id="Jarvis",
                                 title=title or "Jarvis",
                                 msg=msg,
                                 icon=icon_path)
            toast.set_audio(audio.Default, loop=False)
            toast.duration = "short" if dur <= 5 else "long"
            toast.show()
            return True

        if backend == "win10toast":
            # Возможны редкие ошибки WNDPROC на Win11 — используем как запасной вариант
            from win10toast import ToastNotifier
            global _TOASTER
            if _TOASTER is None or not isinstance(_TOASTER, ToastNotifier):
                _TOASTER = ToastNotifier()
            _TOASTER.show_toast(title=title or "Jarvis",
                                msg=msg,
                                duration=dur,
                                icon_path=icon_path,
                                threaded=True)
            return True

    except Exception:
        # Тихий фолбэк — просто не показываем HUD
        return False

    return False
