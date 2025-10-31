# -*- coding: utf-8 -*-
"""
hotword_cmd_stt_llm_tts_gptlink.py — тест вызова GPT из голоса.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.codegpt_bridge import ask_gpt

def main():
    system_prompt = "Ты — голосовой помощник Джарвис. Отвечай кратко и по сути."
    user_prompt = input("Введи запрос к GPT: ")
    reply = ask_gpt(system_prompt, user_prompt)
    print("\n--- Ответ GPT ---\n", reply, "\n")

if __name__ == "__main__":
    main()
