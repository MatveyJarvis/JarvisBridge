import os
import subprocess
import webbrowser

def open_app(app_name: str) -> str:
    """
    Открыть приложение в Windows (notepad, calc, mspaint и т.д.)
    """
    aliases = {
        "блокнот": "notepad",
        "калькулятор": "calc",
        "paint": "mspaint",
        "проводник": "explorer",
        "cmd": "cmd",
        "powershell": "powershell",
    }
    exe = aliases.get(app_name.lower(), app_name)
    try:
        if exe.lower() in ["calc", "notepad", "mspaint", "powershell", "cmd", "explorer"]:
            subprocess.Popen(exe, shell=True)
        else:
            subprocess.Popen([exe], shell=True)
        return f"✅ Открыл приложение: {exe}"
    except Exception as e:
        return f"❌ Не удалось открыть приложение '{app_name}': {e}"

def open_url(url: str) -> str:
    """
    Открыть ссылку в браузере.
    """
    try:
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        webbrowser.open(url, new=2)
        return f"🌐 Открыл ссылку: {url}"
    except Exception as e:
        return f"❌ Не удалось открыть ссылку '{url}': {e}"
