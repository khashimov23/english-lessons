import json, glob, re, difflib, numpy as np, soundfile as sf, librosa, torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import sys
import os
root = os.environ.get("TTS_ROOT", "/home/claude/tts")   # modellar turgan papka (TARTIB.md ga qarang)
torch.set_num_threads(2); D, OUTD = sys.argv[1], sys.argv[2]
proc = WhisperProcessor.from_pretrained(f"{root}/dl/whisper-small-uzbek")
model = WhisperForConditionalGeneration.from_pretrained(f"{root}/dl/whisper-small-uzbek").eval()
texts = json.load(open(f"{D}/texts.json"))
nz = lambda t: re.sub(r"[^a-z' ]", "", re.sub("[ʻʼ‘’`]", "'", t.lower()).replace("-", " ")).strip()
def asr(w, sr):
    feats = proc(librosa.resample(w, orig_sr=sr, target_sr=16000), sampling_rate=16000, return_tensors="pt").input_features
    with torch.no_grad(): ids = model.generate(feats, max_new_tokens=120)
    return proc.batch_decode(ids, skip_special_tokens=True)[0].strip()
best = {}
for f in sorted(glob.glob(f"{D}/pre/pre_*.wav")):
    key = re.search(r"pre_(.*)_s\d+", f).group(1); w, sr = sf.read(f, dtype="float32")
    hop = int(0.01 * sr); rms = np.array([np.sqrt((w[i:i+hop*2]**2).mean()) for i in range(0, len(w)-hop*2, hop)])
    sil = rms < 0.04 * rms.max(); runs = []; i = 0
    while i < len(sil):
        if sil[i]:
            j = i
            while j < len(sil) and sil[j]: j += 1
            if j - i >= 10 and i * 0.01 > 1.0 and j < len(sil) - 20: runs.append((i, j))
            i = j
        else: i += 1
    res = None
    for (i, j) in runs:
        cut = int((i + j) / 2 * hop); tail = w[cut:]; hyp = asr(tail, sr)
        ratio = difflib.SequenceMatcher(None, nz(texts[key]), nz(hyp)).ratio()
        if "alaykum" not in hyp and "quvchi" not in hyp and "aziz" not in hyp:
            res = dict(file=f, cut=round(cut/sr, 2), pause_ms=(j-i)*10, hyp=hyp, ratio=round(ratio, 2)); break
    print(key, f[-8:], res and {k: res[k] for k in ("cut", "pause_ms", "hyp", "ratio")}, flush=True)
    if res and res["ratio"] > best.get(key, {}).get("ratio", 0): best[key] = res
import os; os.makedirs(OUTD, exist_ok=True)
ok = True
for key in texts:
    r = best.get(key)
    if not r or r["ratio"] < 0.85: print("FAIL", key, r); ok = False; continue
    w, sr = sf.read(r["file"], dtype="float32"); s = w[int(r["cut"]*sr):]
    idx = np.where(np.abs(s) > 0.02 * np.abs(s).max())[0]; s = s[max(0, idx[0]-600): idx[-1]+1800]; s = s / np.abs(s).max() * 0.8
    sf.write(f"{OUTD}/{key}.wav", s, sr); print("OK", key, r["file"][-8:], round(len(s)/sr, 2), "|", texts[key], "->", r["hyp"])
print("ALL_OK" if ok else "SOME_FAILED")
