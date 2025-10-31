# debug_scan.py
from pathlib import Path
OUT = Path(__file__).parent / "_out"
files = sorted([p.name for p in OUT.glob("probe_*.mp3")])
print("FOUND:", files)
print("COUNT:", len(files))
