# actions.py
# v2.1.4 — подтверждения для “опасных” действий + pending-исполнение

import os
import re
import json
import threading
import subprocess
import webbrowser
from datetime import datetime, timedelta
from typing import Optional, List, Union, Dict, Any

from dotenv import load_dotenv


def _normalize(text: str) -> str:
    t = (text or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t


def _safe_url(raw: str) -> Optional[str]:
    if not raw:
        return None
    url = raw.strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "https://" + url
    if len(url) > 2048:
        return None
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s]+$", url):
        return None
    return url


def _safe_path(raw: str, allowed_roots: List[str]) -> Optional[str]:
    if not raw:
        return None
    path = os.path.normpath(raw.strip().strip('"').strip("'"))
    abs_path = os.path.abspath(path)
    try:
        abs_lower = abs_path.lower()
        ok = any(abs_lower.startswith(os.path.abspath(r).lower()) for r in allowed_roots)
        if not ok:
            return None
    except Exception:
        return None
    if not os.path.exists(abs_path):
        return None
    return abs_path


class Actions:
    """
    Белый список действий + подтверждение опасных.
    Типы: process, url, url_from_group, folder_from_group, delay.
    Новое:
      - confirm: true в JSON → вместо немедленного исполнения сохраняем pending и просим подтверждение.
      - confirm_execute_if_pending() / cancel_pending()
    """

    def __init__(self):
        load_dotenv()

        self.enabled = os.getenv("ACTIONS_ENABLED", "1").strip() != "0"
        self.log_enabled = os.getenv("ACTIONS_LOG", "1").strip() != "0"
        self.log_path = os.getenv("ACTIONS_LOG_PATH", "logs\\actions.log")
        roots_env = os.getenv("ALLOWED_ROOTS", "C:\\,D:\\")
        self.allowed_roots = [r.strip() for r in roots_env.split(",") if r.strip()]

        bl_env = os.getenv("ACTIONS_BLACKLIST", "не, не надо, не открывай, отмена, стоп")
        self.blacklist = [_normalize(w) for w in bl_env.split(",") if w.strip()]

        cfg_path = os.getenv("ACTIONS_PATH", "config/actions.json")
        self.actions = self._load(cfg_path)
        self.actions.sort(key=lambda a: int(a.get("priority", 0)), reverse=True)

        self.pending_path = os.getenv("PENDING_ACTION_PATH", "temp\\pending_action.json")
        self.confirm_ttl = int(os.getenv("CONFIRM_TTL", "20"))

        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.pending_path), exist_ok=True)

    # ---------- загрузка/лог ----------
    def _load(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("actions", []) if isinstance(data, dict) else []
        except Exception:
            return []

    def _log(self, level: str, msg: str):
        if not self.log_enabled:
            return
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {level.upper()} {msg}\n")
        except Exception:
            pass

    # ---------- pending ----------
    def _save_pending(self, spec: Dict[str, Any], summary: str):
        data = {
            "expires_at": (datetime.now() + timedelta(seconds=self.confirm_ttl)).timestamp(),
            "summary": summary,
            "spec": spec
        }
        with open(self.pending_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        self._log("PENDING", f"created summary='{summary}' spec={spec}")

    def _load_pending(self) -> Optional[Dict[str, Any]]:
        try:
            with open(self.pending_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if datetime.now().timestamp() > float(data.get("expires_at", 0)):
                self._log("PENDING", "expired")
                self._clear_pending()
                return None
            return data
        except Exception:
            return None

    def _clear_pending(self):
        try:
            if os.path.exists(self.pending_path):
                os.remove(self.pending_path)
        except Exception:
            pass

    def confirm_execute_if_pending(self) -> Optional[str]:
        p = self._load_pending()
        if not p:
            return None
        spec = p.get("spec", {})
        self._clear_pending()
        ok = self._execute_spec(spec)
        return "Готово." if ok else "Не удалось выполнить команду."

    def cancel_pending(self) -> Optional[str]:
        if not self._load_pending():
            return None
        self._clear_pending()
        self._log("PENDING", "cancelled")
        return "Отменил."

    # ---------- публичный API ----------
    def try_run(self, user_text: str, debug: bool = False) -> Optional[str]:
        if not self.enabled:
            self._log("INFO", "Actions disabled by env")
            return None

        nt = _normalize(user_text)
        for bad in self.blacklist:
            if bad and bad in nt:
                self._log("INFO", f"Blocked by blacklist: '{bad}' | phrase='{user_text}'")
                return None

        for a in self.actions:
            mtype = str(a.get("match", "")).strip().lower()
            pattern = a.get("pattern")
            say_text = a.get("say") or "Готово."
            atype = str(a.get("type", "")).strip().lower()
            need_confirm = bool(a.get("confirm", False))
            prio = int(a.get("priority", 0))

            m: Optional[re.Match] = None
            if mtype == "regex":
                try:
                    m = re.search(str(pattern), user_text.strip(), flags=re.IGNORECASE)
                except Exception:
                    continue
                if not m:
                    continue
            else:
                if not self._match(mtype, pattern, nt):
                    continue

            # Требуется подтверждение → сохраняем pending и просим подтверждать
            if need_confirm:
                spec, summary = self._make_spec_for_confirm(a, m, user_text)
                if not spec:
                    return "Действие требует подтверждения, но параметры некорректны."
                self._save_pending(spec, summary)
                return f"Нужно подтверждение: {summary}. Скажи «подтверждаю» или «отмена»."

            # Иначе исполняем сразу
            try:
                ok = self._execute_action(a, m, user_text, prio)
                if ok:
                    return say_text
            except Exception as e:
                self._log("ERR", f"exception: {e} | phrase='{user_text}'")
                return "Не удалось выполнить команду."

        return None

    # ---------- helpers ----------
    def _make_spec_for_confirm(self, action: Dict[str, Any], m: Optional[re.Match], phrase: str):
        atype = str(action.get("type", "")).strip().lower()
        if atype == "url_from_group":
            group = action.get("group") or "url"
            if not (m and group in m.groupdict()):
                return None, ""
            url = _safe_url(m.group(group))
            if not url:
                return None, ""
            return ({"type": "url", "url": url}, f"открыть сайт {url}")

        if atype == "folder_from_group":
            group = action.get("group") or "path"
            if not (m and group in m.groupdict()):
                return None, ""
            path = _safe_path(m.group(group), self.allowed_roots)
            if not path:
                return None, ""
            return ({"type": "folder", "path": path}, f"открыть папку {path}")

        if atype == "process":
            cmd = action.get("command")
            if isinstance(cmd, list) and cmd:
                return ({"type": "process", "command": cmd}, f"запустить {cmd[0]}")

        if atype == "url":
            url = _safe_url(action.get("url", ""))
            if url:
                return ({"type": "url", "url": url}, f"открыть сайт {url}")

        return None, ""

    def _execute_spec(self, spec: Dict[str, Any]) -> bool:
        t = spec.get("type")
        if t == "process":
            cmd = spec.get("command")
            subprocess.Popen(cmd, shell=False); self._log("RUN", f"confirm->process cmd={cmd}")
            return True
        if t == "url":
            url = spec.get("url")
            webbrowser.open(url); self._log("RUN", f"confirm->url url={url}")
            return True
        if t == "folder":
            path = spec.get("path")
            subprocess.Popen(["explorer.exe", path], shell=False); self._log("RUN", f"confirm->folder path={path}")
            return True
        return False

    def _execute_action(self, a: Dict[str, Any], m: Optional[re.Match], phrase: str, prio: int) -> bool:
        atype = str(a.get("type", "")).strip().lower()

        if atype == "process":
            cmd = a.get("command")
            if isinstance(cmd, list) and cmd:
                subprocess.Popen(cmd, shell=False)
                self._log("RUN", f"process prio={prio} cmd={cmd} phrase='{phrase}'")
                return True

        elif atype == "url":
            safe = _safe_url(a.get("url"))
            if safe:
                webbrowser.open(safe)
                self._log("RUN", f"url prio={prio} url={safe} phrase='{phrase}'")
                return True

        elif atype == "url_from_group":
            group = a.get("group") or "url"
            if m and group in m.groupdict():
                safe = _safe_url(m.group(group))
                if safe:
                    webbrowser.open(safe)
                    self._log("RUN", f"url_from_group prio={prio} url={safe} phrase='{phrase}'")
                    return True

        elif atype == "folder_from_group":
            group = a.get("group") or "path"
            if m and group in m.groupdict():
                safe = _safe_path(m.group(group), self.allowed_roots)
                if safe:
                    subprocess.Popen(["explorer.exe", safe], shell=False)
                    self._log("RUN", f"folder prio={prio} path={safe} phrase='{phrase}'")
                    return True

        elif atype == "delay":
            sec_group = a.get("seconds_group") or "sec"
            seconds = None
            if m and sec_group in m.groupdict():
                try:
                    seconds = int(m.group(sec_group))
                except Exception:
                    pass
            if seconds is None:
                self._log("ERR", f"delay: bad seconds in phrase='{phrase}'")
                return False
            then = a.get("then") or {}
            # Преобразуем then в spec и запланируем
            spec = {"type": then.get("type"), "command": then.get("command"), "url": then.get("url"), "group": then.get("group")}
            threading.Timer(interval=max(0, seconds), function=self._execute_spec, args=(spec,)).start()
            self._log("RUN", f"delay prio={prio} sec={seconds} phrase='{phrase}' then={then.get('type')}")
            return True

        return False

    def _match(self, mtype: str, pattern: Union[str, List[str]], nt: str) -> bool:
        if mtype == "equals":
            return nt == _normalize(str(pattern))
        if mtype == "contains_any":
            if isinstance(pattern, list):
                return any(_normalize(p) in nt for p in pattern)
            return _normalize(str(pattern)) in nt
        if mtype == "contains_all":
            return isinstance(pattern, list) and all(_normalize(p) in nt for p in pattern)
        return False
