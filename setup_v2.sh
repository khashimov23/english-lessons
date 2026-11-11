#!/usr/bin/env bash
# Yangi tartib uchun bir martalik tayyorgarlik: kutubxonalar va ovoz modellari (~8 GB, 10-20 daqiqa).
# Ishlatish: ./setup_v2.sh      (modellar $TTS_ROOT ga tushadi, sukut bo'yicha ~/tts)
# Kerak: python3.11, git, ffmpeg; tarmoqda github.com, pypi.org, huggingface.co va us.aws.cdn.hf.co ochiq bo'lishi kerak.
set -euo pipefail
cd "$(dirname "$0")"
REPO=$PWD
export TTS_ROOT=${TTS_ROOT:-$HOME/tts}
export HF_HUB_DISABLE_XET=1                      # katta fayllar oddiy CDN orqali olinadi
DL=$TTS_ROOT/dl
mkdir -p "$DL"
which ffmpeg >/dev/null || { echo "ffmpeg topilmadi"; exit 1; }

# 1) python muhiti (bitta muhit hamma narsaga: ovoz, tekshiruv, video)
if [ ! -x "$TTS_ROOT/venv/bin/python" ]; then
  if command -v uv >/dev/null; then
    uv venv -q -p 3.11 "$TTS_ROOT/venv"
    uv pip install -q -p "$TTS_ROOT/venv/bin/python" -r tools/requirements.txt
  else
    python3.11 -m venv "$TTS_ROOT/venv"
    "$TTS_ROOT/venv/bin/pip" install -q -r tools/requirements.txt
  fi
fi
PY=$TTS_ROOT/venv/bin/python
HF="$TTS_ROOT/venv/bin/hf"; [ -x "$HF" ] || HF="$TTS_ROOT/venv/bin/huggingface-cli"

# 2) CosyVoice kodi (aniq versiya)
if [ ! -d "$DL/CosyVoice/third_party/Matcha-TTS/matcha" ]; then
  rm -rf "$DL/CosyVoice"
  git clone -q https://github.com/FunAudioLLM/CosyVoice.git "$DL/CosyVoice"
  git -C "$DL/CosyVoice" checkout -q 074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc
  git -C "$DL/CosyVoice" submodule update --init --recursive -q
fi

# 3) modellar (Hugging Face)
[ -s "$DL/navoiy-tts/emotion_600h_joint.pt" ] || "$HF" download aisha-org/navoiy-tts emotion_600h_joint.pt emotions_40h.json uztts/__init__.py uztts/normalize.py --local-dir "$DL/navoiy-tts" >/dev/null
[ -s "$DL/CosyVoice2-0.5B/flow.pt" ] || "$HF" download FunAudioLLM/CosyVoice2-0.5B CosyVoice-BlankEN/config.json CosyVoice-BlankEN/generation_config.json CosyVoice-BlankEN/merges.txt CosyVoice-BlankEN/model.safetensors CosyVoice-BlankEN/tokenizer_config.json CosyVoice-BlankEN/vocab.json campplus.onnx cosyvoice2.yaml configuration.json flow.pt hift.pt speech_tokenizer_v2.onnx --local-dir "$DL/CosyVoice2-0.5B" >/dev/null
[ -s "$DL/whisper-small-uzbek/model.safetensors" ] || "$HF" download navai-uz/whisper-small-uzbek config.json generation_config.json model.safetensors preprocessor_config.json tokenizer_config.json vocab.json merges.txt added_tokens.json special_tokens_map.json normalizer.json --local-dir "$DL/whisper-small-uzbek" >/dev/null
[ -s "$DL/whisper-base-en/model.safetensors" ] || "$HF" download openai/whisper-base.en config.json generation_config.json model.safetensors preprocessor_config.json tokenizer_config.json vocab.json merges.txt added_tokens.json special_tokens_map.json normalizer.json tokenizer.json --local-dir "$DL/whisper-base-en" >/dev/null

# 4) Navoiy checkpointini CosyVoice yuklovchisi qabul qiladigan ko'rinishga keltirish (epoch/step kalitlarisiz)
if [ ! -s "$DL/CosyVoice2-0.5B/llm.pt" ]; then
  "$PY" -I -c "
import torch, sys
s = torch.load('$DL/navoiy-tts/emotion_600h_joint.pt', map_location='cpu', weights_only=True)
torch.save({k: v for k, v in s.items() if k not in ('epoch', 'step')}, '$DL/CosyVoice2-0.5B/llm.pt')"
fi

# 5) inglizcha ovoz (Kokoro)
mkdir -p "$REPO/models"
[ -s "$REPO/models/kokoro-v1.0.onnx" ] || curl -sSL -o "$REPO/models/kokoro-v1.0.onnx" https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
[ -s "$REPO/models/voices-v1.0.bin" ] || curl -sSL -o "$REPO/models/voices-v1.0.bin" https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

"$PY" -c "import torch, torchaudio, transformers, kokoro_onnx, PIL, soundfile, librosa, onnxruntime, whisper; print('kutubxonalar joyida')"
for f in navoiy-tts/emotion_600h_joint.pt CosyVoice2-0.5B/llm.pt CosyVoice2-0.5B/flow.pt CosyVoice2-0.5B/hift.pt CosyVoice2-0.5B/speech_tokenizer_v2.onnx CosyVoice2-0.5B/CosyVoice-BlankEN/model.safetensors whisper-small-uzbek/model.safetensors whisper-base-en/model.safetensors; do
  [ -s "$DL/$f" ] || { echo "YETISHMAYDI: $f"; exit 1; }
done
echo "tayyor: $TTS_ROOT"
