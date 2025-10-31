# -*- coding: utf-8 -*-
"""gpt_voice_cycle.py — отладка: пошаговые принты + устойчивый TTS"""
import sys, os, subprocess, traceback
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from openai import OpenAI
from modules.codegpt_bridge import ask_gpt

load_dotenv()
os.makedirs("temp", exist_ok=True)

def tts_play(text: str, mp3_path="temp\\gpt_reply.mp3", voice="alloy", model="gpt-4o-mini-tts"):
    print("STEP3: TTS generate…")
    client = OpenAI()

    # 3a) streaming
    try:
        with client.audio.speech.with_streaming_response.create(
            model=model, voice=voice, input=text
        ) as resp:
            resp.stream_to_file(mp3_path)
        print(f"STEP3: streaming saved -> {mp3_path} | size={os.path.getsize(mp3_path)}")
    except Exception as e:
        print("STEP3: streaming failed -> fallback:", repr(e))
        # 3b) non-streaming fallback
        try:
            resp = client.audio.speech.create(model=model, voice=voice, input=text)
            with open(mp3_path, "wb") as f:
                f.write(resp.read())
            print(f"STEP3: fallback saved -> {mp3_path} | size={os.path.getsize(mp3_path)}")
        except Exception as e2:
            print("STEP3: fallback failed:", repr(e2))
            traceback.print_exc()
            return

    # 4) воспроизведение
    try:
        print("STEP4: play (os.startfile)…")
        os.startfile(mp3_path)
        return
    except Exception as e:
        print("STEP4: os.startfile failed:", repr(e))
    try:
        print("STEP4: play (wmplayer)…")
        subprocess.Popen(['cmd','/c','start','wmplayer','/play','/close', mp3_path], shell=True)
    except Exception as e:
        print("STEP4: wmplayer failed:", repr(e))

def main():
    system_prompt = "Ты — голосовой помощник Джарвис. Отвечай кратко и по делу."
    user = input("Скажи задание Джарвису: ")
    print("STEP1: sending to GPT…")
    reply = ask_gpt(system_prompt, user)
    print("STEP2: got reply, len =", len(reply))
    print("\n--- Ответ GPT ---\n", reply, "\n")
    tts_play(reply)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("FATAL:", repr(e))
        traceback.print_exc()
