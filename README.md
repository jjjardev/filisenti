<div align="center">

<img src="logo.png" alt="FiliSenti" width="120">

# FiliSenti

**3-class Filipino sentiment analysis (Negative / Neutral / Positive)**
Tagalog + Hiligaynon · XLM-RoBERTa-large · on-device INT8 · Flutter + ONNX Runtime

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-jjjardev%2Ffilisenti-black.svg)](https://github.com/jjjardev/filisenti)

</div>

---

## Highlights

- **State-of-the-art results**: **0.8915 test F1-macro** — the highest published score for 3-class Filipino sentiment analysis.
- **Bilingual in one model**: trained on TagaSenti (Tagalog) + HiliSenti (Hiligaynon) = **56,781** labeled sentences.
- **Runs fully on-device**: INT8-quantized ONNX model (≈537 MB) executed on the phone via ONNX Runtime — no internet needed after the model is placed.
- **Two frontends**:
  1. **Flutter Android app** (`filisenti_app/`) — production mobile UI with per-sentence color-coded breakdowns, exports, dark mode.
  2. **Local Flask demo** (`app.py`) — quick browser-based visualization of the ONNX model (summary donut, distribution bar, per-sentence cards).

---

## Model Card

| Field | Value |
|---|---|
| **Model** | FiliSenti (fine-tuned `xlm-roberta-large`) |
| **Base model** | XLM-RoBERTa-large — 355M params, 250K Unigram vocab |
| **Task** | 3-class text classification: `Negative`, `Neutral`, `Positive` |
| **Languages** | Tagalog (tl) + Hiligaynon (hil) |
| **Training data** | TagaSenti 35,686 + HiliSenti 21,095 = **56,781 rows** |
| **Split** | Stratified 80 / 10 / 10 (train 45,424 · val 5,679 · test 5,678) |
| **Best val F1-macro** | **0.8895** @ step 5400 (epoch 4.75) |
| **Test F1-macro** | **0.8915** |
| **Test accuracy** | 0.8923 |
| **Per-class F1** | Negative 0.8862 · Neutral 0.8392 · Positive 0.9490 |
| **Per-language F1** | Hiligaynon **0.917** · Tagalog **0.881** |
| **Deployment format** | INT8 dynamic-quantized ONNX (`filisenti_int8.onnx`) |

### Class weights
Inverse-frequency weighting `wᵢ = N_total / (3 · countᵢ)` applied via a custom `CrossEntropyLoss(weight=..., label_smoothing=0.10)`.

### Training hyperparameters
```
learning_rate:     2e-5            optimizer:      adamw_torch_fused
train_batch:       16              grad_accum:     2  (effective 32)
eval_batch:        32              epochs:         5
weight_decay:      0.05            warmup_steps:   312
scheduler:         cosine_with_min_lr (min_lr=1e-6)
eval_steps:        200             early_stop:     3 (patience)
label_smoothing:   0.10            max_grad_norm:  10.0
fp16:              true (CUDA)     grad_checkpointing: true
```

### Text normalisation
- NFKC Unicode normalization
- Laughter collapsing (`hahaha` / `hehehe`)
- Spaced-letter collapsing (`s o b r a n g` → `sob rang`), repeated chars (`sobraaaang` → `sobraang`)
- Reduplication (`ganda-ganda` → `ganda ganda`), `2`-style repeats (`sobra2` → `sobra sobra`)
- **Slang dictionary** for Tagalog (`wla→wala`, `dko→di ko`, `kc→kasi`, `dpt→dapat`, …) and Hiligaynon (`waay→wala`, `ndi→indi`, `gd→gid`, `sbng→subong`, `krn→karon`, `kg→kag`, …)
- **Casing preserved** — XLM-RoBERTa is cased; lowercasing erases Filipino emphasis (`AYAW KO NA` ≠ `ayaw ko na`)

---

## Hugging Face

| Resource | Link |
|---|---|
| GitHub repo | https://github.com/jjjardev/filisenti |
| TagaSenti dataset | https://huggingface.co/datasets/jjjardev/tagasenti |
| HiliSenti dataset | https://huggingface.co/datasets/jjjardev/hilisenti-v1 |
| **FiliSenti model** | **coming soon** — `https://huggingface.co/jjjardev/filisenti` |

> ⚠️ The FP32 safetensors and INT8 ONNX model files are **not yet uploaded** to the Hub.
> They live locally in `assets/` (git-ignored — see `assets/README.md`). Model card, files,
> and metadata will be published at the link above. Once live, the mobile app and demo can
> pull `filisenti_int8.onnx` directly from there.

---

## Repository structure

```
filisenti/
├── app.py                        # Local Flask demo (browser visualization of the ONNX model)
├── requirements.txt              # Python deps for the demo (Flask + ONNX Runtime + tokenizer)
├── logo.png                      # App logo (also used by the demo header)
├── README.md                     # This file
├── .gitignore
│
├── scripts/                      # All Python pipelines
│   ├── FiliSenti.py              # Training pipeline (load datasets → fine-tune → eval → save)
│   ├── quantize_colab_cell.py    # ONNX INT8 quantization (memory-optimized Colab cell, T4)
│   ├── transfer_best_to_drive.py # Copy final model to Drive + prune checkpoints
│   └── prepare_demo.sh           # One-shot setup for the web demo (model + tokenizer)
│
├── assets/                       # ⚠️ git-ignored — model artifacts (see assets/README.md)
│   ├── README.md                 #   Explains what belongs here + where to download it
│   ├── filisenti_int8.onnx       #   INT8 ONNX (537 MB)
│   ├── model.safetensors         #   FP32 original (2.1 GB)
│   ├── tokenizer.json            #   Unigram SentencePiece tokenizer (17 MB)
│   ├── tokenizer_config.json
│   ├── config.json               #   id2label / label2id
│   ├── final_test_confusion_matrix.png
│   ├── confusion_matrices/       #   28 step-wise confusion-matrix PNGs
│   └── images/logo.png
│
└── filisenti_app/                # Flutter Android app
    ├── pubspec.yaml
    ├── lib/                      # Dart source (services, providers, screens, widgets, theme)
    │   ├── main.dart
    │   ├── models/
    │   ├── services/             # tokenizer / inference / file / export / sentence splitter
    │   ├── providers/            # analysis / theme
    │   ├── screens/              # onboarding / home / analysis / results / about
    │   └── widgets/
    ├── assets/
    │   ├── tokenizer/                # bundled tokenizer (tokenizer.json, tokenizer_config.json, config.json)
    │   └── images/logo.png           # bundled logo
    └── android/                  # Gradle config + ProGuard rules
```

---

## Getting started

### Prerequisites

- **Demo**: Python 3.10+; a virtualenv is recommended.
- **Training**: a GPU (Colab T4 or better) for a practical runtime; CPU works but is slow.
- **Flutter app**: Flutter SDK (≥ 3.x), an Android device or emulator.

### 1. Local web demo (`app.py`)

Runs the INT8 ONNX model in your browser with a full visualization UI (summary donut, distribution bar, per-sentence color-coded cards, dark mode).

```bash
# One-shot setup: creates venv, installs deps, wires up model_onnx/
# (uses a local assets/filisenti_int8.onnx if present, otherwise downloads from HF)
./scripts/prepare_demo.sh

# Run
venv/bin/python app.py
```

Open http://127.0.0.1:5000 — type/paste Filipino text, then analyze. The page calls `POST /api` (JSON) with `{"text": "…"}` and returns the full per-sentence breakdown.

### 2. Train the model from scratch

```bash
venv/bin/pip install torch transformers datasets scikit-learn pandas numpy matplotlib seaborn
cd scripts
python FiliSenti.py
```

What it does:

1. Loads **TagaSenti** (`jjjardev/tagasenti`, train split) and **HiliSenti** (`jjjardev/hilisenti-v1`, train + validation).
2. Cleans labels, applies `normalize_filipino`, stratifies an **80/10/10** split.
3. Probes **vocabulary augmentation** — adds up to 150 frequently-fragmented Filipino words as new tokens (embeddings initialized by averaging sub-word embeddings).
4. Computes the **optimal max length** (P99 of a 2,000-sample probe, capped at 128).
5. Fine-tunes XLM-RoBERTa-large with class weights, cosine-with-min-LR, gradient checkpointing, FP16, early stopping.
6. Evaluates on the test set (combined + per-language) and saves the model + tokenizer to `models/filisenti/`.

### 3. Export + quantize to ONNX (INT8)

After training, upload `models/filisenti/` to `MyDrive/FiliSenti/model`, then run `scripts/quantize_colab_cell.py` in Colab (T4):

```python
# scripts/quantize_colab_cell.py — paste into a Colab cell
!pip install onnx onnxruntime -q
```

Key features:

- Loads with `low_cpu_mem_usage=True` to avoid double weight allocation.
- Exports **FP32 ONNX** (opset 18, dynamic batch/sequence, legacy exporter) under `torch.inference_mode()`.
- **Quantizes INT8 in an isolated subprocess** so the ~1.5 GB ONNX `ModelProto` is fully released to the OS on exit — avoids Colab OOM from Python GC fragmentation.
- Produces a **single-file** `filisenti_int8.onnx` (no external `.data` files) so it can be dropped straight into the Flutter app or the web demo.
- Saves the tokenizer + reports compression ratio.

**ONNX model spec**
```
Inputs:   input_ids       int64 [batch, seq_len]
          attention_mask  int64 [batch, seq_len]
Output:   logits          float32 [batch, 3]
Opset:     18
Quant:     INT8 dynamic (QuantType.QInt8, per_channel=True)
```

### 4. Build & run the Flutter Android app

```bash
cd filisenti_app

# Analyze (should report 0 issues)
flutter analyze

# Build release APK (arm64 only — fastest for this device)
flutter build apk --release --target-platform android-arm64

# Install on a connected device
adb install build/app/outputs/flutter-apk/app-release.apk
```

**Download the model** — the 537 MB ONNX is *not* bundled and not in git. Get it from Hugging Face:
`https://huggingface.co/jjjardev/filisenti` → `filisenti_int8.onnx` (once published). Then load it onto the phone:

- **Method A — in-app file picker**: tap *Select .onnx File* on the home screen and choose the downloaded `filisenti_int8.onnx`.
- **Method B — ADB push**:
  ```bash
  adb push filisenti_int8.onnx /sdcard/Android/data/com.example.filisenti_app/files/
  ```
  The app auto-loads the model from the documents directory on startup.

---

## How it works end-to-end

1. **Training** (`scripts/FiliSenti.py`) produces a fine-tuned `xlm-roberta-large` checkpoint → `models/filisenti/`.
2. **Export/quantize** (`scripts/quantize_colab_cell.py`) converts it to INT8 ONNX → `assets/` (or Drive).
3. **Flutter app** (`filisenti_app/`):
   - `TokenizerService` runs a **pure-Dart Unigram SentencePiece** tokenizer reading `tokenizer.json` (no native dependency).
   - `InferenceService` wraps `flutter_onnxruntime` (`OrtSession`, 2 intra-op threads, 30 s timeout).
   - `AnalysisProvider` splits input into sentences, runs each through the model, and aggregates a majority sentiment + per-sentence confidence.
4. **Demo** (`app.py`) mirrors the same flow in Python for browser testing.

---

## Android configuration notes

| Setting | Value | Why |
|---|---|---|
| `isMinifyEnabled` | `false` | R8 strips ONNX Runtime native/JNI bridge classes |
| ProGuard | `-keep class ai.onnxruntime.** { *; }` | Keeps ORT classes |
| `intraOpNumThreads` | `2` | Avoids CPU contention on the 8-core Helio G91 (4 big + 4 little) |
| `session.run()` timeout | 30 s | ORT can deadlock on MediaTek under heavy load |
| ABI filter | `arm64-v8a` | Device target + smaller APK |
| minSdk / targetSdk | 24 / 35 | |

---

## Known issues & fixes

| Issue | Fix |
|---|---|
| R8 stripping ONNX classes | `isMinifyEnabled = false` + ProGuard keep rule |
| Inference deadlock/hang | 30 s timeout on `session.run()` + 2 threads |
| Analysis stuck at 100% | Auto-navigation via `addPostFrameCallback` |
| Tokenizer vocab format | Parses `[["piece", score], …]` arrays, not dicts |
| File picker extension filtering | Use `FileType.any` (ONNX filter unreliable on Android) |
| Colab OOM during quantization | Isolated subprocess quantization (see `scripts/quantize_colab_cell.py`) |

---

## Key technical decisions

- **Why not bundle the model?** A 537 MB APK is impractical and exceeds the Play Store 150 MB limit — the model is sideloaded.
- **Why disable R8?** ONNX Runtime uses JNI + reflection; minification strips the native bridge.
- **Why a custom Dart tokenizer?** `dart_sentencepiece_tokenizer` had compatibility issues with the XLM-RoBERTa SentencePiece format.
- **Why preserve casing?** Filipino social-media sentiment uses uppercase for emphasis; XLM-RoBERTa is a cased model.
- **Why single-file ONNX?** The app and demo load one `.onnx` path; quantization is isolated in a subprocess to control Colab memory without needing external data files.

---

## Next steps

- [ ] Upload FP32 + ONNX model to Hugging Face (`jjjardev/filisenti`) and link it in the README/app docs
- [ ] Release APK with a proper signing key (currently debug-signed)
- [ ] Performance benchmark — inference time per sentence on the Tecno Spark 30
- [ ] Model integrity check (checksum) before loading on-device
- [ ] App store listing (screenshots, description, privacy policy)
- [ ] iOS support (Metal/CoreML delegate)

---

## Credits

Developed by **Jessie James T. Jarder** — Central Philippines State University (CPSU).

- Datasets: [TagaSenti](https://huggingface.co/datasets/jjjardev/tagasenti) · [HiliSenti](https://huggingface.co/datasets/jjjardev/hilisenti-v1)
- Base model: [XLM-RoBERTa-large](https://huggingface.co/xlm-roberta-large)

If you use this work in research, please cite:

```bibtex
@misc{filisenti2026,
  author  = {Jarder, Jessie James T.},
  title   = {FiliSenti: 3-Class Filipino Sentiment Analysis with XLM-RoBERTa-large},
  year    = {2026},
  note    = {Hiligaynon F1 0.917, Tagalog F1 0.881, combined F1 0.8915}
}
```

---

## License

Licensed under the [Apache License, Version 2.0](LICENSE).

Copyright 2026 Jessie James T. Jarder
