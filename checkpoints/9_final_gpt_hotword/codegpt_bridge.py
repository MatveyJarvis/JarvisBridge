# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=_api_key) if _api_key else OpenAI()

def ask_gpt(system, user, model="gpt-4o-mini"):
    r = client.chat.completions.create(model=model,
        messages=[{"role":"system","content":system},
                  {"role":"user","content":user}],
        temperature=0.2)
    return r.choices[0].message.content

def quick_test():
    return ask_gpt("Ты — лаконичный ассистент.","Ответь словом OK.")

if __name__ == "__main__":
    print("TEST_OUTPUT:", quick_test())
