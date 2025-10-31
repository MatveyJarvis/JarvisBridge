import webrtcvad, sounddevice as sd, numpy as np, time

RATE = 16000
FRAME_MS = 30
CHUNK = int(RATE * FRAME_MS / 1000)
DURATION_SEC = 5
vad = webrtcvad.Vad(2)  # агрессивность 0–3

print("=== VAD Probe ===")
print("Говори в микрофон (5 сек)...")
frames = int((DURATION_SEC * 1000) / FRAME_MS)
speech_frames = 0

stream = sd.InputStream(samplerate=RATE, channels=1, dtype="int16")
stream.start()
for i in range(frames):
    data, _ = stream.read(CHUNK)
    active = vad.is_speech(data.tobytes(), RATE)
    level = np.abs(np.frombuffer(data, dtype=np.int16)).mean()
    bar = "█" * int(min(50, level / 200))
    tag = "ГОЛОС" if active else "..."
    print(f"{tag:5s} | {bar}")
    if active:
        speech_frames += 1
    time.sleep(FRAME_MS / 1000.0)
stream.stop()
print(f"\nАктивных кадров речи: {speech_frames}/{frames}")
