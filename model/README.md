# `model/` — model artifacts (not committed to git)

This directory is **git-ignored** because the model files are too large to store
in the repository. They are published on **Hugging Face** instead:

📦 **Model repo:** https://huggingface.co/jjjardev/filisenti

## Files expected here

| File | Size | Source |
|---|---|---|
| `filisenti_int8.onnx` | ~537 MB | INT8 ONNX — download from HF (`filisenti_int8.onnx`) or regenerate with `scripts/quantize_colab_cell.py` |
| `model.safetensors` | ~2.1 GB | FP32 fine-tuned weights (source for re-export) |
| `tokenizer.json` | ~17 MB | XLM-RoBERTa Unigram SentencePiece tokenizer |
| `tokenizer_config.json` | 343 B | Tokenizer config |
| `config.json` | 922 B | Model config + `id2label` / `label2id` |
| `final_test_confusion_matrix.png` | 32 KB | Test-set confusion matrix |
| `confusion_matrices/` | 848 KB | Step-wise training CMs (28 PNGs) |
| `images/logo.png` | 1.4 MB | App logo |

## How to get them

1. Download `filisenti_int8.onnx` from the Hugging Face model repo above
   (`https://huggingface.co/jjjardev/filisenti/resolve/main/filisenti_int8.onnx`),
   **or**
2. Train the model with `scripts/FiliSenti.py`, then quantize with
   `scripts/quantize_colab_cell.py`.

The small tokenizer configs are also bundled in `filisenti_app/assets/tokenizer/`
so a fresh clone can run the local demo without this directory.
