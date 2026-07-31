"""Copy final FiliSenti model to Google Drive & remove intermediate checkpoints."""
import os, shutil, glob, json

from google.colab import drive

SRC  = "models/filisenti"
DST  = "/content/drive/MyDrive/FiliSenti/model"

drive.mount("/content/drive")

# Report best metric
state_path = os.path.join(SRC, "trainer_state.json")
if os.path.exists(state_path):
    with open(state_path) as f:
        state = json.load(f)
    print(f"Best F1 Macro:  {state.get('best_metric', '?'):.4f}")
    print(f"Best step:      {state.get('best_model_checkpoint', '?')}")
    print(f"Global step:    {state.get('global_step', '?')}")

# Copy final model to Drive
os.makedirs(DST, exist_ok=True)
for item in os.listdir(SRC):
    if item.startswith("checkpoint-"):
        continue
    s = os.path.join(SRC, item)
    d = os.path.join(DST, item)
    if os.path.isdir(s):
        shutil.copytree(s, d, dirs_exist_ok=True)
    else:
        shutil.copy2(s, d)
print(f"\nFinal model copied -> {DST}")

# Delete checkpoints
ckpts = sorted(glob.glob(os.path.join(SRC, "checkpoint-*")))
if ckpts:
    for ckpt in ckpts:
        shutil.rmtree(ckpt, ignore_errors=True)
    print(f"Removed {len(ckpts)} checkpoints, freed ~{len(ckpts) * 2.2:.0f} GB")
