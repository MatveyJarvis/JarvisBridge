# list_audio_devices.py  — печатает входные устройства с индексами
import sounddevice as sd
import sys
try:
    devices = sd.query_devices()
except Exception as e:
    print("[ERR]", e)
    sys.exit(1)

print("\n=== INPUT DEVICES ===")
for i, d in enumerate(devices):
    if d.get('max_input_channels', 0) > 0:
        print(f"{i:>3} | {d.get('name','?')} | inputs={d.get('max_input_channels')}")
print("\nPick the index that matches your microphone.")
