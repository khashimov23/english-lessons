#!/usr/bin/env bash
# Maxsus "Xato va to'g'risi" videosini tayyorlaydi: ovoz -> tekshiruv -> video, muqova, izoh.
# Ishlatish: tools/xato.sh xato-01     (specials/xato-01.json dan)   Avval: ./setup_v2.sh
# Natija: voice_uz/ID/*.wav va videos/ID/{ID.mp4, cover.jpg, caption.txt}. Oxirida "XATO_OK ID" chiqishi kerak.
set -uo pipefail
cd "$(dirname "$0")/.."
ID=$1
export TTS_ROOT=${TTS_ROOT:-$HOME/tts}
export HF_HUB_OFFLINE=1 MALLOC_ARENA_MAX=2
PY=$TTS_ROOT/venv/bin/python
D=$TTS_ROOT/ish/$ID
rm -rf "$D"; mkdir -p "$D"/{kokoro,pre,vc}
$PY - "$ID" "$D" <<'P' > "$D/kokoro.log" 2>&1 || { echo "XATO_XATO matn/kokoro"; exit 1; }
import json, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
les, out = json.load(open(f"specials/{sys.argv[1]}.json")), sys.argv[2]
dot = lambda s: s if s[-1] in ".!?" else s + "."
t = {"hook": les["hook_say"]}
for i, it in enumerate(les["items"]):
    t[f"uz{i}"] = dot(it.get("uz_say") or it["uz"])
t["next"] = les["end_say"]
json.dump(t, open(f"{out}/texts.json", "w"), ensure_ascii=False, indent=1)
k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
for i, it in enumerate(les["items"]):
    s, sr = k.create(dot(it["en"]), voice="af_heart", speed=0.8, lang="en-us")
    sf.write(f"{out}/kokoro/en{i}.wav", np.asarray(s, dtype=np.float32), sr)
P
# Ovoz bo'laklab chiqariladi (har bo'lak alohida jarayonda): hammasi birga bo'lsa xotira yetmay qolishi mumkin.
$PY - "$D" <<'P'
import json, os, shutil, sys
D = sys.argv[1]; t = json.load(open(f"{D}/texts.json"))
os.makedirs(f"{D}/b0/kokoro"); [os.makedirs(f"{D}/b0/{x}") for x in ("vc", "pre")]
for f in os.listdir(f"{D}/kokoro"): shutil.copy(f"{D}/kokoro/{f}", f"{D}/b0/kokoro/{f}")
json.dump({}, open(f"{D}/b0/texts.json", "w"))
for n, (k, v) in enumerate(t.items(), 1):
    [os.makedirs(f"{D}/b{n}/{x}") for x in ("kokoro", "vc", "pre")]
    json.dump({k: v}, open(f"{D}/b{n}/texts.json", "w"), ensure_ascii=False)
P
for B in "$D"/b*; do
  $PY tools/2_ovoz_chiqar.py "$B" > "$B/ovoz.log" 2>&1
  grep -q ALL_DONE "$B/ovoz.log" || { tail -5 "$B/ovoz.log"; echo "XATO_XATO ovoz $(basename "$B")"; exit 1; }
  cp "$B"/vc/*.wav "$D"/vc/ 2>/dev/null; cp "$B"/pre/*.wav "$D"/pre/ 2>/dev/null
done
V=voice_uz/$ID; rm -rf "$V"; mkdir -p "$V"
$PY -I tools/3_kes_va_tekshir.py "$D" "$PWD/$V" 2>&1 | grep -E "^OK|^FAIL|ALL_OK|SOME_FAILED" | tee "$D/tekshiruv.log"
grep -q ALL_OK "$D/tekshiruv.log" || { echo "XATO_XATO o'zbekcha tekshiruv"; exit 1; }
cp "$D"/vc/*.wav "$V"/
$PY -I tools/4_inglizcha_tekshir.py "$D/vc" 2>&1 | grep "^EN"
$PY xato_v1.py specials/$ID.json sheet > /dev/null && $PY xato_v1.py specials/$ID.json | tail -1 || { echo "XATO_XATO video"; exit 1; }
[ -s videos/$ID/$ID.mp4 ] && [ -s videos/$ID/cover.jpg ] && echo "XATO_OK $ID" || echo "XATO_XATO fayl yo'q"
