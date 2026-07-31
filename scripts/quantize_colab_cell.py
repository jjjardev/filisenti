# ============================================================
# FILISENTI — ONNX INT8 Quantization (Memory-Optimized for T4)
# ============================================================
# Key change: quantize_dynamic runs in an ISOLATED SUBPROCESS
# so the ~1.5 GB ONNX ModelProto is fully released to the OS
# on exit — no Python GC fragmentation can linger.

!pip install onnx onnxruntime -q

import os, gc, warnings, subprocess, sys
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from google.colab import drive

# ── Suppress cosmetic warnings ──────────────────────────────
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*legacy.*ONNX.*")
warnings.filterwarnings("ignore", message=".*torch.tensor results are registered as constants.*")

# ── Mount ────────────────────────────────────────────────────
drive.mount("/content/drive", force_remount=True)

DRIVE_MODEL_DIR = "/content/drive/MyDrive/FiliSenti/model"
ONNX_OUTPUT_DIR  = "/content/drive/MyDrive/FiliSenti/model_onnx"
os.makedirs(ONNX_OUTPUT_DIR, exist_ok=True)

# ── Free memory at start ────────────────────────────────────
gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()

# ── Load model (low_cpu_mem_usage avoids double-allocation) ──
print("Loading model...")
model = AutoModelForSequenceClassification.from_pretrained(
    DRIVE_MODEL_DIR,
    local_files_only=True,
    low_cpu_mem_usage=True,          # ← weights loaded incrementally; no 2× spike
)
tokenizer = AutoTokenizer.from_pretrained(DRIVE_MODEL_DIR, local_files_only=True)
model.eval()

# ── Export FP32 ONNX ─────────────────────────────────────────
print("Exporting to ONNX (FP32)...")
onnx_fp32_path = os.path.join(ONNX_OUTPUT_DIR, "filisenti.onnx")
quant_path     = os.path.join(ONNX_OUTPUT_DIR, "filisenti_int8.onnx")
dummy = tokenizer("Sample text", return_tensors="pt")

with torch.inference_mode():        # ← tighter than torch.no_grad(); no autograd metadata
    torch.onnx.export(
        model,
        (dummy["input_ids"], dummy["attention_mask"]),
        onnx_fp32_path,
        opset_version=18,
        do_constant_folding=True,
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids":      {0: "batch_size", 1: "sequence_length"},
            "attention_mask":  {0: "batch_size", 1: "sequence_length"},
            "logits":          {0: "batch_size"},
        },
        dynamo=False,                # legacy exporter — stable with dynamic_axes
    )

# ── Free ALL PyTorch memory ──────────────────────────────────
del model, dummy
gc.collect()                        # first pass: direct refs
if torch.cuda.is_available():
    torch.cuda.empty_cache()
gc.collect()                        # second pass: cyclic refs freed by first pass

# ── Quantize in isolated subprocess ──────────────────────────
# quantize_dynamic calls onnx.load() internally, holding ~1.5 GB
# of protobuf objects.  A child process guarantees the OS reclaims
# *every byte* on exit — no Python GC fragmentation.
print("Quantizing INT8 in isolated subprocess...")
quant_script = os.path.join(ONNX_OUTPUT_DIR, "_quantize_tmp.py")
with open(quant_script, "w") as f:
    f.write(f"""
from onnxruntime.quantization import quantize_dynamic, QuantType
print("Loading ONNX model for quantization...")
quantize_dynamic(
    model_input="{onnx_fp32_path}",
    model_output="{quant_path}",
    weight_type=QuantType.QInt8,
    per_channel=True,
    use_external_data_format=False,
)
print("Quantization succeeded.")
""")
result = subprocess.run(
    [sys.executable, quant_script],
    capture_output=True, text=True, timeout=600,
)
os.remove(quant_script)

print(result.stdout)
if result.returncode != 0:
    raise RuntimeError(f"Quantization failed:\n{result.stderr}")

# ── Save tokenizer ───────────────────────────────────────────
tokenizer.save_pretrained(ONNX_OUTPUT_DIR)

# ── Report ───────────────────────────────────────────────────
def total_onnx_size(base_path):
    total = os.path.getsize(base_path)
    data_path = base_path + ".data"
    if os.path.exists(data_path):
        total += os.path.getsize(data_path)
    return total

fp32_mb = total_onnx_size(onnx_fp32_path) / 1e6
int8_mb = total_onnx_size(quant_path) / 1e6

print(f"\n✅ Done! Files saved in: {ONNX_OUTPUT_DIR}")
print(f"   FP32 : {fp32_mb:>8.1f} MB  →  filisenti.onnx")
print(f"   INT8 : {int8_mb:>8.1f} MB  →  filisenti_int8.onnx")
print(f"   Ratio: {fp32_mb / int8_mb:.1f}× compression")
print("   Single-file INT8 model — drop filisenti_int8.onnx straight into the Flutter app or app.py.")
