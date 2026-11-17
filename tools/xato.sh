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
# Ovoz bo'laklab chiqariladi (har bo'lak alohida jarayonda, bitta urug' bilan): hammasi birga bo'lsa xotira yetmay qoladi.
bolak() {  # bolak PAPKA URUG' — bir marta qayta urinadi
  for _try in 1 2; do
    SEEDS=$2 $PY tools/2_ovoz_chiqar.py "$1" > "$1/ovoz.log" 2>&1
    grep -q ALL_DONE "$1/ovoz.log" && { cp "$1"/vc/*.wav "$D"/vc/ 2>/dev/null; cp "$1"/pre/*.wav "$D"/pre/ 2>/dev/null; return 0; }
  done
  tail -3 "$1/ovoz.log"; return 1
}
mk() {  # mk PAPKA KALIT — bitta o'zbekcha gap uchun ish papkasi
  mkdir -p "$1"/{kokoro,vc,pre}
  $PY -c "import json,sys; t=json.load(open(sys.argv[1]+'/texts.json')); json.dump({sys.argv[3]: t[sys.argv[3]]}, open(sys.argv[2]+'/texts.json','w'), ensure_ascii=False)" "$D" "$1" "$2"
}
mkdir -p "$D"/b_en/{vc,pre}; cp -r "$D/kokoro" "$D/b_en/kokoro"; echo "{}" > "$D/b_en/texts.json"
bolak "$D/b_en" 42 || { echo "XATO_XATO ovoz inglizcha"; exit 1; }
KEYS=$($PY -c "import json,sys; print(' '.join(json.load(open(sys.argv[1]+'/texts.json'))))" "$D")
for K in $KEYS; do mk "$D/b_$K" "$K"; bolak "$D/b_$K" 42 || { echo "XATO_XATO ovoz $K"; exit 1; }; done
V=voice_uz/$ID; rm -rf "$V"; mkdir -p "$V"
tekshir() { $PY -I tools/3_kes_va_tekshir.py "$D" "$PWD/$V" 2>&1 | grep -E "^OK|^FAIL|ALL_OK|SOME_FAILED" > "$D/tekshiruv.log"; }
tekshir
if ! grep -q ALL_OK "$D/tekshiruv.log"; then      # o'tmagan gaplar ikkinchi urug' bilan qayta chiqariladi
  for K in $(grep "^FAIL" "$D/tekshiruv.log" | awk '{print $2}'); do mk "$D/c_$K" "$K"; bolak "$D/c_$K" 7 || { echo "XATO_XATO ovoz $K"; exit 1; }; done
  tekshir
fi
cat "$D/tekshiruv.log"
grep -q ALL_OK "$D/tekshiruv.log" || { echo "XATO_XATO o'zbekcha tekshiruv"; exit 1; }
cp "$D"/vc/*.wav "$V"/
$PY -I tools/4_inglizcha_tekshir.py "$D/vc" 2>&1 | grep "^EN"
$PY xato_v1.py specials/$ID.json sheet > /dev/null && $PY xato_v1.py specials/$ID.json | tail -1 || { echo "XATO_XATO video"; exit 1; }
[ -s videos/$ID/$ID.mp4 ] && [ -s videos/$ID/cover.jpg ] && echo "XATO_OK $ID" || echo "XATO_XATO fayl yo'q"
