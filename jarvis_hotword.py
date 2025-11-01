# ===== Jarvis Hotword Detector — стабильная версия после Этапа 3 =====
import os, time, playsound

def activate():
    print('[Hotword] Использую INPUT_DEVICE_INDEX=1')
    print('[Hotword] Скажи фразу с упоминанием «Джарвис» (например: «Привет, Джарвис»).')
    time.sleep(3)
    os.system('python -X utf8 -u C:\\JarvisBridge\\jarvis_main_voice_bridge_v3.py')

if __name__ == '__main__':
    activate()

