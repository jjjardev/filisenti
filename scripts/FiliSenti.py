import os
import re
import unicodedata
import multiprocessing
from collections import Counter

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import seaborn as sns

from datasets import Dataset, Features, Value, load_dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    EarlyStoppingCallback,
    Trainer,
    TrainerCallback,
    TrainingArguments,
)

CFG = {
    "tagasenti_repo": "jjjardev/tagasenti",
    "hilisenti_repo": "jjjardev/hilisenti-v1",
    "output_dir":     "models/filisenti",
    "model_ckpt":     "xlm-roberta-large",
    "test_size":      0.20,
    "val_from_held":  0.50,
    "seed":           42,
    "max_len_percentile": 99,
    "max_len_cap":         128,
    "max_len_sample":      2_000,
    "learning_rate":    2e-5,
    "train_batch":      16,
    "eval_batch":       32,
    "grad_accum":       2,
    "num_epochs":       5,
    "weight_decay":     0.05,
    "warmup_steps":     312,
    "min_lr":           1e-6,
    "eval_steps":       200,
    "early_stop":       3,
    "label_smoothing":  0.10,
}

LABEL_NAMES = ["Negative", "Neutral", "Positive"]
ID2LABEL    = {i: n for i, n in enumerate(LABEL_NAMES)}
LABEL2ID    = {n: i for i, n in enumerate(LABEL_NAMES)}

os.makedirs(CFG["output_dir"], exist_ok=True)

# ============================================================
# TEXT NORMALISATION — shared across Tagalog and Hiligaynon
# ============================================================
# Casing is intentionally preserved — XLM-RoBERTa is a cased SentencePiece
# model. Lowercasing erases the emphasis signal common in Filipino
# social-media sentiment ("AYAW KO NA" ≠ "ayaw ko na").
#
# Slang patterns cover both Tagalog and Hiligaynon abbreviations.

_SLANG = {
    # Tagalog / general Filipino
    r"\bwla\b":     "wala",
    r"\blng\b":     "lang",
    r"\bnlng\b":    "nalang",
    r"\bna lng\b":  "nalang",
    r"\bdko\b":     "di ko",
    r"\bgnito\b":   "ganito",
    r"\bgnyan\b":   "ganyan",
    r"\bgnun\b":    "ganun",
    r"\bsakin\b":   "sa akin",
    r"\bpru\b":     "pero",
    r"\bkc\b":      "kasi",
    r"\bksi\b":     "kasi",
    r"\bky\b":      "kay",
    r"\bnman\b":    "naman",
    r"\bnmn\b":     "naman",
    r"\bmeron\b":   "mayroon",
    r"\bsya\b":     "siya",
    r"\bxa\b":      "siya",
    r"\bxia\b":     "siya",
    r"\bnya\b":     "niya",
    r"\bikw\b":     "ikaw",
    r"\bmng\b":     "mang",
    r"\bdpt\b":     "dapat",
    r"\bdba\b":     "di ba",
    r"\bdiba\b":    "di ba",
    # Hiligaynon
    r"\bwaay\b":    "wala",
    r"\bway\b":     "wala",
    r"\bndi\b":     "indi",
    r"\bnd\b":      "indi",
    r"\bgd\b":      "gid",
    r"\bgud\b":     "gid",
    r"\bmn\b":      "man",
    r"\bbl\b":      "bala",
    r"\btni\b":     "tani",
    r"\btne\b":     "tani",
    r"\bnyo\b":     "ninyo",
    r"\bcmu\b":     "sa imo",
    r"\bsakn\b":    "sa akon",
    r"\bskn\b":     "sa akon",
    r"\bkw\b":      "ikaw",
    r"\bsbng\b":    "subong",
    r"\bkrn\b":     "karon",
    r"\bhlng\b":    "halong",
    r"\bpro\b":     "pero",
    r"\bkg\b":      "kag",
    r"\bkng\b":     "kon",
    r"\bkun\b":     "kon",
}

_COMPILED_SLANG = [(re.compile(p), r) for p, r in _SLANG.items()]


def normalize_filipino(text) -> str:
    """Light normalisation for Filipino (Tagalog + Hiligaynon) social-media text."""
    if pd.isna(text):
        return ""
    text = unicodedata.normalize("NFKC", str(text))
    text = re.sub(r"\b(?:ha){2,}h*\b", "hahaha", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:he){2,}h*\b", "hehehe", text, flags=re.IGNORECASE)
    text = re.sub(r"\b([A-Za-z]{3,})2\b", r"\1 \1", text)
    text = re.sub(r"\b(\w+)-\1\b", r"\1 \1", text)
    for pattern, replacement in _COMPILED_SLANG:
        text = pattern.sub(replacement, text)
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["label"] = df["label"].astype(str).str.strip().str.replace('"', "", regex=False)
    df["label"] = pd.to_numeric(df["label"], errors="coerce")
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)
    return df[df["label"].isin([0, 1, 2])].reset_index(drop=True)


# ============================================================
# LOAD DATASETS
# ============================================================
features = Features({"sentence": Value("string"), "label": Value("string")})

print("=" * 60)
print("FILISENTI — UNIFIED FILIPINO SENTIMENT MODEL")
print("=" * 60)

print(f"\nLoading TagaSenti from {CFG['tagasenti_repo']} …")
tagasenti = load_dataset(CFG["tagasenti_repo"], split="train", features=features)
tagasenti_df = clean_labels(pd.DataFrame(tagasenti))
tagasenti_df["language"] = "tagalog"
print(f"  {len(tagasenti_df)} Tagalog rows")

print(f"Loading HiliSenti from {CFG['hilisenti_repo']} …")
hilisenti_train = load_dataset(CFG["hilisenti_repo"], split="train", features=features)
hilisenti_val   = load_dataset(CFG["hilisenti_repo"], split="validation", features=features)
hilisenti_df = clean_labels(pd.concat([
    pd.DataFrame(hilisenti_train),
    pd.DataFrame(hilisenti_val),
], ignore_index=True))
hilisenti_df["language"] = "hiligaynon"
print(f"  {len(hilisenti_df)} Hiligaynon rows (train={len(hilisenti_train)}, val={len(hilisenti_val)})")

df = pd.concat([tagasenti_df, hilisenti_df], ignore_index=True)
print(f"\nCombined: {len(df)} rows")
print(f"  Tagalog:    {(df['language'] == 'tagalog').sum()}")
print(f"  Hiligaynon: {(df['language'] == 'hiligaynon').sum()}")
print(f"\nLabel distribution:\n{df['label'].value_counts().sort_index()}")

# ============================================================
# STRATIFIED SPLIT 80 / 10 / 10
# ============================================================
train_df, temp_df = train_test_split(
    df, test_size=CFG["test_size"], stratify=df["label"], random_state=CFG["seed"]
)
val_df, test_df = train_test_split(
    temp_df, test_size=CFG["val_from_held"], stratify=temp_df["label"], random_state=CFG["seed"]
)
train_df = train_df.reset_index(drop=True)
val_df   = val_df.reset_index(drop=True)
test_df  = test_df.reset_index(drop=True)

print(f"\nTrain : {len(train_df)} | Val : {len(val_df)} | Test : {len(test_df)}")

# ============================================================
# NORMALISE
# ============================================================
print("Normalising text …")
for split_df in (train_df, val_df, test_df):
    split_df["sentence"] = split_df["sentence"].apply(normalize_filipino)

# ============================================================
# VOCABULARY AUGMENTATION — add frequent fragmented tokens
# ============================================================
tokenizer = AutoTokenizer.from_pretrained(CFG["model_ckpt"])
old_tokenizer = AutoTokenizer.from_pretrained(CFG["model_ckpt"])


def find_fragmented_words(tokenizer, texts, sample_size=2000):
    sample = texts[:sample_size] if len(texts) > sample_size else texts
    all_words = []
    for text in sample:
        all_words.extend(re.findall(r"\b\w{4,}\b", text.lower()))
    word_freq = Counter(all_words)
    fragmented = []
    for word, count in word_freq.most_common(300):
        tokens = tokenizer.tokenize(word)
        if len(tokens) > 2:
            fragmented.append((word, tokens, count))
    return fragmented


fragmented = find_fragmented_words(tokenizer, train_df["sentence"].tolist())
new_tokens = [word for word, _, count in fragmented if count >= 3 and len(word) > 3][:150]

if new_tokens:
    tokenizer.add_tokens(new_tokens)
    print(f"\nAdded {len(new_tokens)} new tokens to vocabulary")

# ============================================================
# OPTIMAL MAX LENGTH
# ============================================================
sample_n = min(CFG["max_len_sample"], len(train_df))
sample_texts = train_df["sentence"].sample(sample_n, random_state=CFG["seed"]).tolist()
probe_lengths = [len(tokenizer.encode(t, add_special_tokens=True, truncation=False)) for t in sample_texts]
print(
    f"\nToken-length distribution (n={sample_n}):  "
    f"p50={np.percentile(probe_lengths, 50):.0f}  "
    f"p90={np.percentile(probe_lengths, 90):.0f}  "
    f"p95={np.percentile(probe_lengths, 95):.0f}  "
    f"p99={np.percentile(probe_lengths, 99):.0f}  "
    f"max={max(probe_lengths)}"
)
optimal_max_length = min(int(np.percentile(probe_lengths, CFG["max_len_percentile"])), CFG["max_len_cap"])
print(f"Optimal max length: {optimal_max_length}\n")

# ============================================================
# TOKENISATION
# ============================================================
def tokenize_fn(batch):
    return tokenizer(batch["sentence"], padding=False, truncation=True, max_length=optimal_max_length)


def build_dataset(split_df: pd.DataFrame) -> Dataset:
    return Dataset.from_pandas(split_df[["sentence", "label"]].reset_index(drop=True))


# num_proc = min(multiprocessing.cpu_count(), 4) # Original line
num_proc = 1 # Changed to 1 to avoid multiprocessing issues with tokenizer serialization
print(f"Tokenising with {num_proc} workers …")
_map_kw = dict(batched=True, remove_columns=["sentence"], num_proc=num_proc)
tokenized_train = build_dataset(train_df).map(tokenize_fn, **_map_kw)
tokenized_val   = build_dataset(val_df).map(tokenize_fn, **_map_kw)
tokenized_test  = build_dataset(test_df).map(tokenize_fn, **_map_kw)

# ============================================================
# MODEL
# ============================================================
model = AutoModelForSequenceClassification.from_pretrained(
    CFG["model_ckpt"],
    num_labels=3,
    id2label=ID2LABEL,
    label2id=LABEL2ID,
)

if new_tokens:
    model.resize_token_embeddings(len(tokenizer))
    with torch.no_grad():
        embeddings = model.get_input_embeddings().weight
        for word in new_tokens:
            new_id = tokenizer.convert_tokens_to_ids(word)
            old_ids = old_tokenizer.encode(word, add_special_tokens=False)
            if old_ids:
                mean_emb = embeddings[old_ids].mean(dim=0)
                embeddings[new_id] = mean_emb
    print(f"Resized embeddings to: {len(tokenizer)}")

# ============================================================
# CLASS WEIGHTS
# ============================================================
counts = train_df["label"].value_counts().sort_index()
n_total = len(train_df)
class_weights = [n_total / (3 * counts[i]) for i in range(3)]
class_weights_tensor = torch.tensor(class_weights, dtype=torch.float)
print(f"Class weights: {class_weights_tensor}")

# ============================================================
# METRICS
# ============================================================
_last_eval: dict = {}


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    _last_eval["preds"] = preds
    _last_eval["labels"] = labels
    f1_cls   = f1_score(labels, preds, average=None, labels=[0, 1, 2], zero_division=0)
    prec_cls = precision_score(labels, preds, average=None, labels=[0, 1, 2], zero_division=0)
    rec_cls  = recall_score(labels, preds, average=None, labels=[0, 1, 2], zero_division=0)
    return {
        "accuracy":           accuracy_score(labels, preds),
        "balanced_accuracy":  balanced_accuracy_score(labels, preds),
        "f1_macro":           f1_score(labels, preds, average="macro", zero_division=0),
        "f1_negative":        f1_cls[0],
        "f1_neutral":         f1_cls[1],
        "f1_positive":        f1_cls[2],
        "precision_negative": prec_cls[0],
        "precision_neutral":  prec_cls[1],
        "precision_positive": prec_cls[2],
        "recall_negative":    rec_cls[0],
        "recall_neutral":     rec_cls[1],
        "recall_positive":    rec_cls[2],
    }


# ============================================================
# DETAILED LOGGING CALLBACK
# ============================================================
class DetailedLogCallback(TrainerCallback):
    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is None:
            return
        step = state.global_step
        epoch = f"{state.epoch:.2f}" if state.epoch is not None else "?"
        parts = [f"Step {step}  |  Ep {epoch}"]

        if "loss" in logs:
            parts.append(f"Loss {logs['loss']:.4f}")
        if "learning_rate" in logs:
            lr = logs["learning_rate"]
            parts.append(f"LR {lr:.2e}")
        if "grad_norm" in logs:
            parts.append(f"GradNorm {logs['grad_norm']:.4f}")

        if len(parts) > 2:
            print("  " + "  |  ".join(parts))

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        if metrics is None:
            return
        step = state.global_step
        epoch = f"{state.epoch:.2f}" if state.epoch is not None else "?"
        print(f"\n{'='*65}")
        print(f"  EVAL @ Step {step}  |  Ep {epoch}")
        print(f"{'='*65}")
        print(f"  Val Loss:      {metrics.get('eval_loss', '?'):.4f}" if 'eval_loss' in metrics else "")
        print(f"  Accuracy:      {metrics.get('eval_accuracy', '?'):.4f}" if 'eval_accuracy' in metrics else "")
        print(f"  Balanced Acc:  {metrics.get('eval_balanced_accuracy', '?'):.4f}" if 'eval_balanced_accuracy' in metrics else "")
        print(f"  F1 Macro:      {metrics.get('eval_f1_macro', '?'):.4f}" if 'eval_f1_macro' in metrics else "")
        print(f"  F1 [Neg/Neu/Pos]:  {metrics.get('eval_f1_negative', '?'):.4f} / {metrics.get('eval_f1_neutral', '?'):.4f} / {metrics.get('eval_f1_positive', '?'):.4f}")
        print(f"  Prec[Neg/Neu/Pos]: {metrics.get('eval_precision_negative', '?'):.4f} / {metrics.get('eval_precision_neutral', '?'):.4f} / {metrics.get('eval_precision_positive', '?'):.4f}")
        print(f"  Rec [Neg/Neu/Pos]: {metrics.get('eval_recall_negative', '?'):.4f} / {metrics.get('eval_recall_neutral', '?'):.4f} / {metrics.get('eval_recall_positive', '?'):.4f}")
        lr_hist = [m.get("learning_rate", 0) for m in state.log_history if "learning_rate" in m]
        if lr_hist:
            print(f"  Current LR:    {lr_hist[-1]:.2e}")


# ============================================================
# CONFUSION MATRIX CALLBACK
# ============================================================
class ConfusionMatrixCallback(TrainerCallback):
    def on_evaluate(self, args, state, control, **kwargs):
        if not _last_eval:
            return
        preds  = _last_eval["preds"]
        labels = _last_eval["labels"]
        step   = state.global_step
        self._save_cm(labels, preds, step, args.output_dir)
        print(f"\n--- Classification Report (step {step}) ---")
        print(classification_report(labels, preds, target_names=LABEL_NAMES, digits=4))
        print(f"Prediction distribution:\n{pd.Series(preds).value_counts().sort_index()}\n")

    @staticmethod
    def _save_cm(labels, preds, step: int, output_dir: str):
        cm = confusion_matrix(labels, preds)
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                    xticklabels=LABEL_NAMES, yticklabels=LABEL_NAMES, ax=ax)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_title(f"Confusion Matrix — step {step}")
        cm_dir = os.path.join(output_dir, "confusion_matrices")
        os.makedirs(cm_dir, exist_ok=True)
        fig.savefig(os.path.join(cm_dir, f"cm_step_{step}.png"), bbox_inches="tight")
        plt.close(fig)
        print(f"  CM saved → {os.path.join(cm_dir, f'cm_step_{step}.png')}")


# ============================================================
# CUSTOM TRAINER
# ============================================================
class CustomTrainer(Trainer):
    def __init__(self, class_weights: torch.Tensor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        loss_fct = nn.CrossEntropyLoss(
            weight=self.class_weights.to(logits.device),
            label_smoothing=self.args.label_smoothing_factor,
        )
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


# ============================================================
# TRAINING ARGUMENTS
# ============================================================
training_args = TrainingArguments(
    output_dir=CFG["output_dir"],
    eval_strategy="steps",
    eval_steps=CFG["eval_steps"],
    save_strategy="steps",
    save_steps=CFG["eval_steps"],
    save_total_limit=0,
    load_best_model_at_end=True,
    metric_for_best_model="f1_macro",
    greater_is_better=True,
    learning_rate=CFG["learning_rate"],
    per_device_train_batch_size=CFG["train_batch"],
    per_device_eval_batch_size=CFG["eval_batch"],
    gradient_accumulation_steps=CFG["grad_accum"],
    num_train_epochs=CFG["num_epochs"],
    weight_decay=CFG["weight_decay"],
    warmup_steps=CFG["warmup_steps"],
    lr_scheduler_type="cosine_with_min_lr",
    lr_scheduler_kwargs={"min_lr": CFG["min_lr"]},
    optim="adamw_torch_fused",
    gradient_checkpointing=True,
    fp16=torch.cuda.is_available(),
    label_smoothing_factor=CFG["label_smoothing"],
    logging_strategy="steps",
    logging_steps=50,
    logging_first_step=True,
    report_to="tensorboard",
    seed=CFG["seed"],
)

# ============================================================
# BUILD TRAINER & TRAIN
# ============================================================
trainer = CustomTrainer(
    class_weights=class_weights_tensor,
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_val,
    data_collator=DataCollatorWithPadding(tokenizer),
    compute_metrics=compute_metrics,
    callbacks=[
        EarlyStoppingCallback(early_stopping_patience=CFG["early_stop"]),
        DetailedLogCallback(),
        ConfusionMatrixCallback(),
    ],
)

print("\nStarting training …\n")
trainer.train()

# ============================================================
# TEST SET EVALUATION
# ============================================================
print("\nEvaluating on test set …")
test_output   = trainer.predict(tokenized_test, metric_key_prefix="test")
test_labels   = test_output.label_ids
test_preds_np = np.argmax(test_output.predictions, axis=-1)
print(f"Test metrics: {test_output.metrics}\n")

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(
    confusion_matrix(test_labels, test_preds_np),
    annot=True, fmt="d", cmap="Greens",
    xticklabels=LABEL_NAMES, yticklabels=LABEL_NAMES, ax=ax,
)
ax.set_title("FiliSenti — Combined Test Set Confusion Matrix")
ax.set_xlabel("Predicted")
ax.set_ylabel("True")
fig.savefig(os.path.join(CFG["output_dir"], "final_test_confusion_matrix.png"), bbox_inches="tight")
plt.show()
plt.close(fig)

print("\nFinal test classification report:")
print(classification_report(test_labels, test_preds_np, target_names=LABEL_NAMES))

# ============================================================
# PER-LANGUAGE EVALUATION
# ============================================================
print("\n" + "=" * 60)
print("PER-LANGUAGE BREAKDOWN")
print("=" * 60)

for lang in ["tagalog", "hiligaynon"]:
    lang_df = test_df[test_df["language"] == lang].reset_index(drop=True)
    if len(lang_df) == 0:
        continue
    lang_ds = build_dataset(lang_df)
    lang_ds = lang_ds.map(tokenize_fn, batched=True, remove_columns=["sentence"], num_proc=num_proc)
    lang_out = trainer.predict(lang_ds, metric_key_prefix=lang)
    lang_preds = np.argmax(lang_out.predictions, axis=-1)
    print(f"\n--- {lang.title()} ({len(lang_df)} samples) ---")
    print(classification_report(lang_out.label_ids, lang_preds, target_names=LABEL_NAMES))

# ============================================================
# SAVE
# ============================================================
trainer.save_model(CFG["output_dir"])
tokenizer.save_pretrained(CFG["output_dir"])
print(f"\nModel + tokeniser saved → {CFG['output_dir']}")
