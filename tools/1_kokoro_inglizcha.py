"""lesson.py dagi inglizcha bo'laklarni Kokoro bilan alohida fayllarga chiqaradi."""
import sys, json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
les, out, root = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
k = Kokoro(f"{root}/models/kokoro-v1.0.onnx", f"{root}/models/voices-v1.0.bin")
dot = lambda s: s if s[-1] in ".!?" else s + "."
segs = []
for i, it in enumerate(les["items"]):
    segs += [(f"slow{i}", dot(it["en"]), 0.75), (f"norm{i}", dot(it["en"]), 0.9), (f"rep{i}", dot(it["en"]), 0.85)]
segs.append(("example", les["example"]["en"], 0.8))
for sid, text, speed in segs:
    s, sr = k.create(text, voice="af_heart", speed=speed, lang="en-us")
    sf.write(f"{out}/{sid}.wav", np.asarray(s, dtype=np.float32), sr); print(sid, text, round(len(s)/sr, 2))
