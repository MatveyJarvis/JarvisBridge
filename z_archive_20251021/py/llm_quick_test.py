# -*- coding: utf-8 -*-
from llm_client import ask_llm

if __name__ == "__main__":
    msgs = [
        {"role": "system", "content": "Ты отвечаешь кратко и дружелюбно на русском."},
        {"role": "user", "content": "Кто ты и как можешь помочь? В 1–2 предложения."}
    ]
    print("LLM:", ask_llm(msgs, max_output_tokens=120))
