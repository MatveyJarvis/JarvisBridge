# tools/list_sd_devices.py
import sounddevice as sd

print("=== INPUT DEVICES ===")
for i, info in enumerate(sd.query_devices()):
    if info["max_input_channels"] > 0:
        print(f"[{i}] {info['name']} | SR={int(info['default_samplerate'])} | CH={info['max_input_channels']}")
print("\nTip: выбери явный 'Microphone ...' или 'Микрофон ...', а не 'Набор микрофонов' / 'Stereo Mix'.")
