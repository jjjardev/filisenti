# `model_onnx/` — demo model directory (not committed to git)

This directory is **git-ignored**. It is the local folder that `app.py` (the
Flask demo) expects next to it, containing the INT8 ONNX model and tokenizer.

## What goes here

| File | Purpose |
|---|---|
| `filisenti_int8.onnx` | INT8 ONNX model (537 MB) |
| `tokenizer.json` | Unigram SentencePiece tokenizer |
| `tokenizer_config.json` | Tokenizer config |
| `config.json` | Model config + `id2label` / `label2id` |

## How to create it

Run the one-shot setup script (creates `model_onnx/`, downloads the model from
Hugging Face if not found locally, and installs the demo dependencies):

```bash
./scripts/prepare_demo.sh
```

The script uses `model/filisenti_int8.onnx` when present locally, otherwise it
downloads from:
`https://huggingface.co/jjjardev/filisenti/resolve/main/onnx/filisenti_int8.onnx`
