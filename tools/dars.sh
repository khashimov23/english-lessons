#!/usr/bin/env bash
# Bitta darsni boshidan oxirigacha tayyorlaydi: ovoz -> tekshiruv -> video, muqova, izoh.
# Ishlatish: tools/dars.sh NN     (masalan: tools/dars.sh 06)   Avval: ./setup_v2.sh
# Natija: voice_uz/dars-NN/*.wav va videos/dars-NN/{dars-NN.mp4, cover.jpg, caption.txt}
# Oxirgi qatorda "DARS_OK NN" chiqsa hammasi joyida; "DARS_XATO" chiqsa videoni ishlatmang.
set -uo pipefail
cd "$(dirname "$0")/.."
N=$1
export TTS_ROOT=${TTS_ROOT:-$HOME/tts}
export HF_HUB_OFFLINE=1
PY=$TTS_ROOT/venv/bin/python
D=$TTS_ROOT/ish/dars-$N
rm -rf "$D"; mkdir -p "$D"
$PY -I tools/0_matnlar.py lessons/dars-$N.json "$D" > "$D/matnlar.log" || { echo "DARS_XATO matn"; exit 1; }
$PY tools/1_kokoro_inglizcha.py lessons/dars-$N.json "$D/kokoro" . > "$D/kokoro.log" 2>&1 || { echo "DARS_XATO kokoro"; exit 1; }
$PY tools/2_ovoz_chiqar.py "$D" > "$D/ovoz.log" 2>&1
grep -q ALL_DONE "$D/ovoz.log" || { tail -5 "$D/ovoz.log"; echo "DARS_XATO ovoz"; exit 1; }
V=voice_uz/dars-$N; mkdir -p "$V"
$PY -I tools/3_kes_va_tekshir.py "$D" "$PWD/$V" 2>&1 | grep -E "^OK|^FAIL|ALL_OK|SOME_FAILED" | tee "$D/tekshiruv.log"
grep -q ALL_OK "$D/tekshiruv.log" || { echo "DARS_XATO o'zbekcha tekshiruv"; exit 1; }
cp "$D"/vc/*.wav "$V"/ && cp voice_uz/ref/turn.wav "$V"/turn.wav
$PY -I tools/4_inglizcha_tekshir.py "$D/vc" 2>&1 | grep "^EN"
$PY lesson_v2.py lessons/dars-$N.json sheet > /dev/null && $PY lesson_v2.py lessons/dars-$N.json | tail -1 || { echo "DARS_XATO video"; exit 1; }
[ -s videos/dars-$N/dars-$N.mp4 ] && [ -s videos/dars-$N/cover.jpg ] && echo "DARS_OK $N" || echo "DARS_XATO fayl yo'q"
