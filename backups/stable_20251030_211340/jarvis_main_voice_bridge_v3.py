# -*- coding: utf-8 -*-
import os, sys, time, json, wave, traceback
from datetime import datetime
from dotenv import load_dotenv; load_dotenv()
ROOT=os.path.abspath(os.path.dirname(__file__)); sys.path.insert(0,ROOT) if ROOT not in sys.path else None

import openai
import jarvis_hotword_vad as jhv
from jarvis_hotword_vad import VadConfig, record_utterance_vad

openai.api_key = os.getenv("OPENAI_API_KEY")
SR=int(os.getenv("SAMPLE_RATE","16000"))
jhv.USE_WEBRTCVAD = os.getenv("USE_WEBRTCVAD","0") not in ("0","false","False")
VFM=int(os.getenv("VAD_FRAME_MS","20")); VSM=int(os.getenv("VAD_MAX_SILENCE_MS","900"))
VAG=int(os.getenv("VAD_AGGRESSIVENESS","3")); VPRE=int(os.getenv("VAD_PREROLL_MS","250")); VPOST=int(os.getenv("VAD_POSTROLL_MS","300"))
MUTE=int(os.getenv("MUTE_AFTER_TTS_MS","800"))

BASE=r"C:\JarvisBridge"; TEMP=os.path.join(BASE,"temp"); LOGS=os.path.join(BASE,"logs")
A_IN=os.path.join(TEMP,"voice_in.wav"); TTS_OUT=os.path.join(TEMP,"tts_out.mp3"); TTS_LISTEN=os.path.join(TEMP,"tts_listen.mp3"); LOG=os.path.join(LOGS,"voice_dialog.jsonl")
os.makedirs(TEMP,exist_ok=True); os.makedirs(LOGS,exist_ok=True)

def _log(d):
    d["ts"]=datetime.now().isoformat(timespec="seconds")
    with open(LOG,"a",encoding="utf-8") as f: f.write(json.dumps(d,ensure_ascii=False)+"\n")

def speak(text,out):
    s=openai.audio.speech.create(model="gpt-4o-mini-tts",voice="alloy",input=text)
    with open(out,"wb") as f: f.write(s.read()); print(f"[tts] {out}")

def record_once():
    cfg=VadConfig(frame_ms=VFM,max_silence_ms=VSM,aggressiveness=VAG,preroll_ms=VPRE,postroll_ms=VPOST); cfg.samplerate=SR
    pcm=record_utterance_vad(cfg)
    with wave.open(A_IN,"wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm)
    dur=len(pcm)/(SR*2); print(f"[rec] {A_IN} dur={dur:.2f}s"); return dur

def stt():
    with open(A_IN,"rb") as f: r=openai.audio.transcriptions.create(model="gpt-4o-mini-transcribe",file=f)
    t=(r.text or "").strip(); print(f"[stt] {t}"); return t

def llm(q):
    r=openai.chat.completions.create(model="gpt-4o-mini",messages=[{"role":"user","content":q}])
    a=r.choices[0].message.content.strip(); print(f"[llm] {a}"); return a

def main():
    print(f"=== Jarvis Full (VAD={jhv.USE_WEBRTCVAD}, frame={VFM}ms, sil={VSM}ms, mute={MUTE}ms)")
    speak("Слушаю",TTS_LISTEN); time.sleep(MUTE/1000)
    dur=record_once(); q=stt(); a=llm(q if q else "Скажи текущее время простыми словами."); speak(a,TTS_OUT)
    _log({"cfg":{"frame_ms":VFM,"sil_ms":VSM,"mute_ms":MUTE,"webrtc":jhv.USE_WEBRTCVAD},"dur_s":round(dur,2),"stt":q,"llm":a}); print("[Jarvis] Готово.")

if __name__=="__main__":
    try: main()
    except Exception as e: print("[ERR]",e); traceback.print_exc()
