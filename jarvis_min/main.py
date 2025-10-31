# main.py — единый тестовый запуск: STT -> LLM -> TTS
from __future__ import annotations
import os
import argparse
from pathlib import Path
from openai import OpenAI
import dotenv

# локальные модули
from stt_openai import transcribe
from tts_openai import say
from recorder import record_wav

# автоподгрузка .env
dotenv.load_dotenv()

def ensure_env() -> tuple[str, int]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY пуст. Заполни .env")
    try:
        sec = int(os.getenv("RECORD_SECONDS", "5"))
    except Exception:
        sec = 5
    return model, sec

def chat(model: str, user_text: str) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Ты — Jarvis. Отвечай кратко и по делу."},
            {"role": "user", "content": user_text},
        ],
    )
    return resp.choices[0].message.content.strip()

def run(audio_path: Path | None) -> None:
    model, rec_seconds = ensure_env()

    # 1) получаем аудио
    if audio_path is None:
        print(f"[Jarvis] Запись микрофона {rec_seconds} сек...")
        wav = Path("input.wav")
        record_wav(str(wav), seconds=rec_seconds)
        audio_path = wav
    else:
        audio_path = Path(audio_path)

    # 2) STT
    print(f"[Jarvis] Распознаю: {audio_path.name}")
    text = transcribe(str(audio_path))
    print(f"[STT] → {text}")

    if not text.strip():
        say("Не удалось распознать речь. Повторите, пожалуйста.")
        return

    # 3) LLM
    print(f"[Jarvis] Думаю...")
    reply = chat(model, text)
    print(f"[LLM] → {reply}")

    # 4) TTS
    print(f"[Jarvis] Озвучиваю ответ...")
    out_file = say(reply)
    print(f"[TTS] Файл: {out_file}")

def main():
    parser = argparse.ArgumentParser(description="Jarvis voice test")
    parser.add_argument("--file", type=str, help="готовый аудиофайл (wav/mp3)")
    args = parser.parse_args()
    run(Path(args.file) if args.file else None)

if __name__ == "__main__":
    main()
