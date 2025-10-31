import sounddevice as sd

def main():
    print("=== INPUT DEVICES (only with inputs) ===")
    for i, dev in enumerate(sd.query_devices()):
        if dev.get("max_input_channels", 0) > 0:
            sr = int(dev.get("default_samplerate", 0))
            name = dev.get("name", "")
            print(f"[{i}] {name} | inputs={dev['max_input_channels']} | default_sr={sr}")

if __name__ == "__main__":
    main()
