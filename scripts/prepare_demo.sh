#!/usr/bin/env bash
#
# Prepare the local web demo (app.py) for a fresh clone:
#  1. Wires up model_onnx/ (which app.py expects) using the bundled tokenizer
#  2. Uses the local model/filisenti_int8.onnx if present, otherwise downloads
#     it from Hugging Face
#
# Usage:  ./scripts/prepare_demo.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="$ROOT/model_onnx"
ONNX_DEST="$MODEL_DIR/filisenti_int8.onnx"
TOKENIZER_SRC="$ROOT/filisenti_app/assets/tokenizer"
LOCAL_ONNX="$ROOT/model/filisenti_int8.onnx"
HF_URL="https://huggingface.co/jjjardev/filisenti/resolve/main/filisenti_int8.onnx"

mkdir -p "$MODEL_DIR"

# 1. ONNX model
if [ -f "$LOCAL_ONNX" ]; then
  echo "Using local model: $LOCAL_ONNX"
  cp "$LOCAL_ONNX" "$ONNX_DEST"
else
  echo "Local model not found."
  if command -v wget >/dev/null 2>&1; then
    echo "Downloading from Hugging Face: $HF_URL"
    wget -O "$ONNX_DEST" "$HF_URL"
  elif command -v curl >/dev/null 2>&1; then
    echo "Downloading from Hugging Face: $HF_URL"
    curl -L -o "$ONNX_DEST" "$HF_URL"
  else
    echo "Please download $HF_URL and place it at:"
    echo "  $ONNX_DEST"
    exit 1
  fi
fi

# 2. Tokenizer files (bundled with the Flutter app)
cp "$TOKENIZER_SRC/tokenizer.json" \
   "$TOKENIZER_SRC/tokenizer_config.json" \
   "$TOKENIZER_SRC/config.json" \
   "$MODEL_DIR/"

# 3. Python deps
if [ -d "$ROOT/venv" ]; then
  "$ROOT/venv/bin/pip" install -q -r "$ROOT/requirements.txt"
  echo "Dependencies installed in venv/."
else
  echo "No venv/ found. Run:  python3 -m venv venv && venv/bin/pip install -r requirements.txt"
fi

echo
echo "Demo ready. Start it with:"
echo "  venv/bin/python app.py"
echo "Then open http://127.0.0.1:5000"
