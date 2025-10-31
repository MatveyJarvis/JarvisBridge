import pyttsx3
import os

_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()  # SAPI5 на Windows
        # громкость и скорость по умолчанию
        _engine.setProperty('volume', 1.0)     # 0.0..1.0
        _engine.setProperty('rate', 180)       # 150-200 обычно ок

        # выбор голоса: из .env или авто-русский
        wanted = os.getenv("TTS_VOICE", "").strip().lower()
        voices = _engine.getProperty('voices')

        def pick_voice():
            # если указан TTS_VOICE — ищем по подстроке
            if wanted:
                for v in voices:
                    if wanted in (v.name or "").lower():
                        return v.id
            # иначе пытаемся найти русское имя (Irina/Pavel/Svetlana и т.п.)
            for v in voices:
                name = (v.name or "").lower()
                if any(tag in name for tag in ["irina", "pavel", "svetlana", "russian", "ru-ru"]):
                    return v.id
            # иначе оставляем голос по умолчанию
            return None

        vid = pick_voice()
        if vid:
            _engine.setProperty('voice', vid)
    return _engine

def say(text: str):
    eng = _get_engine()
    eng.say(text)
    eng.runAndWait()
