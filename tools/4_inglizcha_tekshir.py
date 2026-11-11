import sys, glob, os, soundfile as sf, librosa, torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import os
root = os.environ.get("TTS_ROOT", "/home/claude/tts")   # modellar turgan papka (TARTIB.md ga qarang)
torch.set_num_threads(2)
proc = WhisperProcessor.from_pretrained(f"{root}/dl/whisper-base-en"); model = WhisperForConditionalGeneration.from_pretrained(f"{root}/dl/whisper-base-en").eval()
for f in sorted(glob.glob(sys.argv[1] + "/*.wav")):
    w, sr = sf.read(f, dtype="float32")
    feats = proc(librosa.resample(w, orig_sr=sr, target_sr=16000), sampling_rate=16000, return_tensors="pt").input_features
    with torch.no_grad(): ids = model.generate(feats, max_new_tokens=40)
    print("EN", os.path.basename(f), f"{len(w)/sr:.2f}s", "->", proc.batch_decode(ids, skip_special_tokens=True)[0].strip(), flush=True)
