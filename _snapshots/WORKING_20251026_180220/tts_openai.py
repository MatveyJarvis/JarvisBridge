import os
from openai import OpenAI
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.playback import play
import tempfile

# --- простая конвертация чисел в слова (0..99) ---
_UNITS = {
    0: "ноль", 1: "один", 2: "два", 3: "три", 4: "четыре",
    5: "пять", 6: "шесть", 7: "семь", 8: "восемь", 9: "девять",
    10: "десять", 11: "одиннадцать", 12: "двенадцать", 13: "тринадцать",
    14: "четырнадцать", 15: "пятнадцать", 16: "шестнадцать",
    17: "семнадцать", 18: "восемнадцать", 19: "девятнадцать"
}
_TENS = {20: "двадцать", 30: "тридцать", 40: "сорок", 50: "пятьдесят",
         60: "шестьдесят", 70: "семьдесят", 80: "восемьдесят", 90: "девяносто"}

def _num_to_ru_0_99(n: int) -> str:
    if 0 <= n < 20:
        return _UNITS[n]
    if 20 <= n < 100:
        d = (n // 10) * 10
        r = n % 10
        return _TENS[d] + ("" if r == 0 else f" {_UNITS[r]}")
    return str(n)

def _polish_text(text: str) -> str:
    t = (text or "").strip()
    # если ответ — чисто число, озвучим по-русски словами (до 99)
    if t.isdigit():
        try:
            n = int(t)
            if 0 <= n < 100:
                t = _num_to_ru_0_99(n)
        except Exception:
            pass
    # гарантируем финальную точку — у alloy так звучит мягче
    if t and t[-1] not in ".!?…":
        t += "."
    return t

def say(text: str):
    """
    Озвучивает текст голосом Джарвиса (OpenAI TTS).
    Настройки берутся из .env:
      - TTS_VOICE (например, alloy)
      - OPENAI_TTS_MODEL (например, gpt-4o-mini-tts)
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("❌ Не найден ключ OPENAI_API_KEY в .env")

    client = OpenAI(api_key=api_key)
    voice = os.getenv("TTS_VOICE", os.getenv("OPENAI_TTS_VOICE", "alloy")).strip()
    model = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts").strip()

    polished = _polish_text(text)
    print(f"[TTS] ▶ Озвучиваю ({voice}) → {polished}")

    # Создаем временный mp3, чтобы исключить блокировки устройства вывода
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        temp_path = temp_audio.name
        with client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=polished
        ) as response:
            response.stream_to_file(temp_path)

    # Воспроизводим
    sound = AudioSegment.from_mp3(temp_path)
    play(sound)

    # Убираем временный файл
    try:
        os.remove(temp_path)
    except Exception:
        pass

    print("[TTS] ✅ Озвучивание завершено.\n")

if __name__ == "__main__":
    say("16")
