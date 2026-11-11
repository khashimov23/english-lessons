#!/usr/bin/env bash
# Ovoz chiqarilgandan keyin: kesish + tekshirish + video, muqova, izoh.
# Ishlatish: tools/5_yigish.sh NN ISH_PAPKA   (masalan: tools/5_yigish.sh 03 ish/dars-03)
# PY_TEKSHIR — transformers o'rnatilgan python, PY_VIDEO — pillow/soundfile o'rnatilgan python.
set -e
cd "$(dirname "$0")/.."
N=$1; D=$2; V=voice_uz/dars-$N
PY_TEKSHIR=${PY_TEKSHIR:-python3}; PY_VIDEO=${PY_VIDEO:-python3}
mkdir -p "$V"
$PY_TEKSHIR -I tools/3_kes_va_tekshir.py "$D" "$PWD/$V" 2>&1 | grep -E "^OK|^FAIL|ALL_OK|SOME_FAILED"
cp "$D"/vc/*.wav "$V"/
cp voice_uz/ref/turn.wav "$V"/turn.wav
$PY_TEKSHIR -I tools/4_inglizcha_tekshir.py "$D/vc" 2>&1 | grep "^EN"
$PY_VIDEO lesson_v2.py lessons/dars-$N.json | tail -1
