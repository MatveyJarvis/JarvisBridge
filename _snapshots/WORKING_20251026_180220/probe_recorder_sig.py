import inspect, sys
print("=== probe: recorder.record_wav signature ===")
try:
    import recorder
except Exception as e:
    print("[err] import recorder:", e)
    sys.exit(1)

try:
    sig = inspect.signature(recorder.record_wav)
    print("signature ->", sig)
    params = list(sig.parameters.items())
    for i, (name, p) in enumerate(params, 1):
        print(f"  {i}. {name}: kind={p.kind}, default={p.default}")
    try:
        src = inspect.getsource(recorder.record_wav)
        lines = src.strip().splitlines()
        print("\n--- first 25 lines of recorder.record_wav ---")
        for ln in lines[:25]:
            print(ln.rstrip())
        print("--- end snippet ---")
    except Exception as e:
        print("[warn] cannot show source:", e)
except Exception as e:
    print("[err] inspect signature:", e)
