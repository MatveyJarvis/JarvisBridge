import os, json, time

LOG_PATH = r"C:\JarvisBridge\logs\voice_dialog.jsonl"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

entry = {
    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    "stt": "probe",
    "reply": "ok",
    "note": "manual probe"
}

with open(LOG_PATH, "a", encoding="utf-8") as f:
    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    f.flush()
    os.fsync(f.fileno())

print("WROTE:", LOG_PATH)
