# tests/tts_quick_test.py
import os, pathlib, uuid, subprocess, time, shutil
from pydub.generators import Sine
from pydub import AudioSegment

BASE = pathlib.Path(__file__).resolve().parent.parent
TEMP = BASE / "temp"
TEMP.mkdir(exist_ok=True)

# Перенастроим системные TMP/TEMP, чтобы pydub писал именно сюда
os.environ["TMP"] = str(TEMP)
os.environ["TEMP"] = str(TEMP)
os.environ["TMPDIR"] = str(TEMP)

def _ffplay_available() -> bool:
    return shutil.which("ffplay") is not None

def _play_wav(path: pathlib.Path):
    if _ffplay_available():
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)],
            check=False
        )
    else:
        # fallback через pydub (теперь у нас есть права на TEMP)
        snd = AudioSegment.from_file(path, format="wav")
        from pydub.playback import play
        play(snd)

def beep(ms=600, freq=880):
    fname = f"beep_{freq}_{ms}_{uuid.uuid4().hex}.wav"
    fpath = TEMP / fname
    snd = Sine(freq).to_audio_segment(duration=ms).apply_gain(-3)
    snd.export(fpath, format="wav")
    print(f"[TEST] Beep {freq}Hz {ms}ms -> {fpath.name}")
    _play_wav(fpath)
    try:
        fpath.unlink(missing_ok=True)
    except Exception:
        pass

if __name__ == "__main__":
    print("[TEST] === Проверка локального звука (без интернета) ===")
    beep(400, 880)
    time.sleep(0.2)
    beep(400, 660)
    print("[TEST] Если слышны 2 коротких сигнала — вывод звука в порядке.")
