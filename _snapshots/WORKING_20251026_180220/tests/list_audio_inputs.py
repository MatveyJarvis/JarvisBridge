# -*- coding: utf-8 -*-
import sounddevice as sd

def main():
    print("=== INPUT DEVICES (only max input channels > 0) ===")
    default_in, default_out = sd.default.device
    print(f"Default IN index: {default_in}")
    print()
    for i, dev in enumerate(sd.query_devices()):
        if dev.get('max_input_channels', 0) > 0:
            mark = " (DEFAULT)" if i == default_in else ""
            print(f"[{i}] {dev['name']} | in={dev['max_input_channels']} out={dev['max_output_channels']}{mark}")
    print("\nПодскажи номер (index) твоего микрофона из списка.")

if __name__ == "__main__":
    main()
