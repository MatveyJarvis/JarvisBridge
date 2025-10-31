import sounddevice as sd

print("=== AUDIO DEVICES ===")
for i, d in enumerate(sd.query_devices()):
    print(f"[{i:>2}] {d['name']} | in:{d['max_input_channels']} out:{d['max_output_channels']}")
print("\nDefaults:", sd.default)
