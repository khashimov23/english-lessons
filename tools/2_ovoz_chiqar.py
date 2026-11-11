"""CPU adaptation of navoiy-tts/inference.py (same steps, fp16 off, no CUDA check)."""
import sys, json, time, random, torch, torchaudio, soundfile as sf
import os
root = os.environ.get("TTS_ROOT", "/home/claude/tts")   # modellar turgan papka (TARTIB.md ga qarang)
sys.path.insert(0, f"{root}/dl/CosyVoice"); sys.path.insert(0, f"{root}/dl/CosyVoice/third_party/Matcha-TTS")
sys.path.insert(0, f"{root}/dl/navoiy-tts")
torch.set_num_threads(2)
def _load(path, *a, **k):
    w, sr = sf.read(str(path), dtype="float32", always_2d=True)
    return torch.from_numpy(w.T.copy()), sr
torchaudio.load = _load
from cosyvoice.cli.cosyvoice import CosyVoice2
from uztts.normalize import normalize

cfg = {}
emos = {e["uz"]: e for e in json.load(open(f"{root}/dl/navoiy-tts/emotions_40h.json"))}
model = CosyVoice2(f"{root}/dl/CosyVoice2-0.5B", load_jit=False, load_trt=False, fp16=False)
state = torch.load(f"{root}/dl/navoiy-tts/emotion_600h_joint.pt", map_location="cpu", weights_only=True)
for k in ("state_dict", "model", "llm"):
    if isinstance(state.get(k), dict): state = state[k]
inc = model.model.llm.load_state_dict(state, strict=False)
print("missing", len(inc.missing_keys), "unexpected", len(inc.unexpected_keys), flush=True)
model.model.llm.eval()

import glob, os
D = sys.argv[1]
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "voice_uz", "ref", "ovoz2.wav")   # doimiy ovoz namunasi
for f in sorted(glob.glob(f"{D}/kokoro/*.wav")):
    random.seed(42); torch.manual_seed(42); t0 = time.perf_counter()
    with torch.inference_mode():
        a = torch.cat([r["tts_speech"].cpu() for r in model.inference_vc(f, R, stream=False, speed=1.0)], dim=1)
    sf.write(f"{D}/vc/{os.path.basename(f)}", a.squeeze().numpy(), 24000); print("VC", os.path.basename(f), round(a.shape[-1]/24000, 2), round(time.perf_counter()-t0), flush=True)
PRE = "Assalomu alaykum, aziz o'quvchilar!"
for sd in (42, 7):
  for name, text in json.load(open(f"{D}/texts.json")).items():
    random.seed(sd); torch.manual_seed(sd); t0 = time.perf_counter()
    with torch.inference_mode():
        a = torch.cat([r["tts_speech"].cpu() for r in model.inference_instruct2(normalize(PRE + " " + text, mode="infer"), emos["xursand"]["instruct"].strip() + "<|endofprompt|>", R, stream=False, speed=1.0, text_frontend=False)], dim=1)
    sf.write(f"{D}/pre/pre_{name}_s{sd}.wav", a.squeeze().numpy(), 24000); print("UZ", name, sd, round(a.shape[-1]/24000, 1), round(time.perf_counter()-t0), flush=True)
print("ALL_DONE")
