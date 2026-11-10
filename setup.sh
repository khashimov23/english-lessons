#!/usr/bin/env bash
# Bir martalik tayyorgarlik: kutubxonalar va bepul ovoz modeli (GitHub'dan).
set -e
cd "$(dirname "$0")"
pip install -q --break-system-packages kokoro-onnx soundfile pillow numpy 2>/dev/null || pip install -q kokoro-onnx soundfile pillow numpy
mkdir -p models
[ -s models/kokoro-v1.0.onnx ] || curl -sSL -o models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
[ -s models/voices-v1.0.bin ] || curl -sSL -o models/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
which ffmpeg >/dev/null || { echo "ffmpeg topilmadi"; exit 1; }
echo "tayyor"
