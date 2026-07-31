import os
import re
import json
import numpy as np
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from transformers import AutoTokenizer
import onnxruntime as ort

app = Flask(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model_onnx")
ONNX_PATH = os.path.join(MODEL_DIR, "filisenti_int8.onnx")
LOGO_DIR = os.path.dirname(__file__)
LABEL_NAMES = ["Negative", "Neutral", "Positive"]

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
session = ort.InferenceSession(ONNX_PATH, providers=["CPUExecutionProvider"])

MAX_LEN = 128


def softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()


def predict(text):
    inputs = tokenizer(text, return_tensors="np", truncation=True, max_length=MAX_LEN)
    logits = session.run(["logits"], {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"],
    })[0]
    probs = softmax(logits[0])
    pred = int(np.argmax(probs))
    return pred, probs


def split_sentences(text):
    parts = re.split(r"(?<=[.!?\n])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def analyze(text):
    sentences = split_sentences(text)
    results = []
    counts = {n: 0 for n in LABEL_NAMES}
    for s in sentences:
        pred, probs = predict(s)
        label = LABEL_NAMES[pred]
        counts[label] += 1
        results.append({
            "text": s,
            "label": label,
            "confidence": float(probs[pred]),
            "scores": {n: float(p) for n, p in zip(LABEL_NAMES, probs)},
        })
    total = len(results)
    percentages = {n: (counts[n] / total * 100 if total else 0.0) for n in LABEL_NAMES}
    majority = max(LABEL_NAMES, key=lambda n: counts[n]) if total else "Neutral"
    return {
        "sentences": results,
        "counts": counts,
        "percentages": percentages,
        "total": total,
        "majority": majority,
    }


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FiliSenti — Filipino Sentiment Demo</title>
<style>
:root {
    --bg: #F1F5F9; --card: #FFFFFF; --text: #0F172A; --muted: #64748B;
    --border: #E2E8F0; --primary: #4F46E5; --primary-dark: #4338CA;
    --shadow: 0 4px 24px rgba(15, 23, 42, .08);
}
[data-theme="dark"] {
    --bg: #0F172A; --card: #1E293B; --text: #F1F5F9; --muted: #94A3B8;
    --border: #334155; --shadow: 0 4px 24px rgba(0, 0, 0, .35);
}
* { box-sizing: border-box; }
body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    transition: background .3s, color .3s;
}
.wrap { max-width: 720px; margin: 0 auto; padding: 24px 16px 64px; }

/* header */
header { display: flex; align-items: center; gap: 14px; margin-bottom: 22px; flex-wrap: wrap; }
.logo {
    width: 132px; height: 132px; border-radius: 12px; flex: none;
    object-fit: cover;
}
header h1 { font-size: 22px; margin: 0; }
header p { margin: 0; color: var(--muted); font-size: 13px; }
.theme-btn {
    margin-left: auto; border: 1px solid var(--border); background: var(--card);
    color: var(--text); border-radius: 10px; padding: 8px 12px; cursor: pointer; font-size: 14px;
}

.card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 16px; padding: 20px; box-shadow: var(--shadow);
    margin-bottom: 18px;
}
.card h2 { margin: 0 0 12px; font-size: 16px; }

/* input */
textarea {
    width: 100%; min-height: 110px; resize: vertical; padding: 12px 14px;
    font-size: 15px; line-height: 1.5; font-family: inherit;
    border: 1px solid var(--border); border-radius: 10px; background: var(--bg);
    color: var(--text); outline: none;
}
textarea:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(79,70,229,.15); }
.meta { display: flex; align-items: center; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
.meta .count { color: var(--muted); font-size: 12px; margin-right: auto; }
.chip {
    border: 1px solid var(--border); background: var(--card); color: var(--muted);
    font-size: 12px; padding: 4px 10px; border-radius: 999px; cursor: pointer;
}
.chip:hover { color: var(--primary); border-color: var(--primary); }
.btn-row { display: flex; gap: 10px; margin-top: 14px; }
.btn {
    flex: 1; border: none; border-radius: 10px; padding: 12px 16px;
    font-size: 15px; font-weight: 600; cursor: pointer;
    background: var(--primary); color: #fff; transition: background .2s;
}
.btn:hover { background: var(--primary-dark); }
.btn:disabled { opacity: .6; cursor: not-allowed; }
.btn.ghost {
    flex: 0 0 auto; background: transparent; color: var(--muted);
    border: 1px solid var(--border);
}
.spinner {
    display: none; width: 18px; height: 18px; margin-right: 8px;
    border: 2px solid rgba(255,255,255,.4); border-top-color: #fff;
    border-radius: 50%; animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* summary */
.summary { display: flex; gap: 20px; align-items: center; flex-wrap: wrap; }
.badge {
    display: inline-block; padding: 5px 12px; border-radius: 999px;
    font-size: 13px; font-weight: 700;
}
.maj-block { flex: 1; min-width: 160px; }
.maj-block .badge { font-size: 20px; padding: 8px 16px; }
.maj-pct { font-size: 28px; font-weight: 800; margin-top: 6px; }
.maj-sub { color: var(--muted); font-size: 13px; }
.count-pills { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.count-pill { font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 999px; }

/* donut */
.donut-box { display: flex; flex-direction: column; align-items: center; gap: 10px; }
.donut-wrap { position: relative; width: 150px; height: 150px; }
.donut { width: 150px; height: 150px; border-radius: 50%; }
.donut-hole {
    position: absolute; inset: 26px; background: var(--card); border-radius: 50%;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    text-align: center;
}
.donut-hole .lbl { font-size: 11px; color: var(--muted); }
.donut-hole .val { font-size: 18px; font-weight: 800; }
.legend { display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
.legend .row { display: flex; align-items: center; gap: 8px; }
.legend .dot { width: 10px; height: 10px; border-radius: 3px; flex: none; }
.legend .pct { margin-left: auto; font-weight: 700; }

/* distribution bar */
.dist-label { display: flex; justify-content: space-between; color: var(--muted); font-size: 12px; margin-bottom: 6px; }
.dist-bar { display: flex; height: 12px; border-radius: 6px; overflow: hidden; background: var(--bg); }
.dist-bar div { height: 100%; transition: width .5s ease; }

/* sentences */
.sent {
    border: 1px solid var(--border); border-radius: 12px; padding: 12px 14px;
    margin-bottom: 10px; background: var(--card); animation: fade .4s ease;
}
@keyframes fade { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
.sent-top { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.sent-top .conf { margin-left: auto; font-size: 13px; font-weight: 700; }
.sent-text { margin: 0 0 8px; font-size: 15px; line-height: 1.45; }
.bar { height: 6px; border-radius: 3px; background: var(--bg); overflow: hidden; }
.bar > div { height: 100%; border-radius: 3px; transition: width .5s ease; }
.scores-line { display: flex; gap: 12px; margin-top: 6px; font-size: 11px; color: var(--muted); flex-wrap: wrap; }

.error {
    background: rgba(239,68,68,.1); color: #EF4444; border: 1px solid rgba(239,68,68,.3);
    border-radius: 10px; padding: 10px 14px; font-size: 14px; margin-bottom: 16px;
}
.hidden { display: none; }
footer { text-align: center; color: var(--muted); font-size: 12px; margin-top: 26px; }
footer code { background: var(--card); border: 1px solid var(--border); padding: 2px 6px; border-radius: 5px; }
@media (max-width: 520px) { .summary { flex-direction: column; align-items: stretch; } .donut-box { flex-direction: row; justify-content: center; } }
</style>
</head>
<body>
<div class="wrap">

<header>
    <div class="logo"><img src="/logo.png" alt="FiliSenti" style="width:132px;height:132px;border-radius:12px"></div>
    <div>
        <h1>FiliSenti</h1>
        <p>Tagalog / Hiligaynon sentiment · XLM-RoBERTa-large INT8 · on-device model</p>
    </div>
    <button class="theme-btn" onclick="toggleTheme()" title="Toggle theme">◐ Theme</button>
</header>

<div id="error-box" class="error hidden"></div>

<div class="card">
    <h2>Analyze text</h2>
    <textarea id="text" placeholder="Type or paste Filipino text… e.g. 'Ang ganda ng serbisyo niyo! Sulit na sulit! Wala lang, okay naman.'"></textarea>
    <div class="meta">
        <span class="count" id="count">0 characters</span>
        <button class="chip" onclick="useExample(0)">Positive</button>
        <button class="chip" onclick="useExample(1)">Negative</button>
        <button class="chip" onclick="useExample(2)">Mixed</button>
    </div>
    <div class="btn-row">
        <button class="btn" id="analyze-btn" onclick="analyze()"><span class="spinner" id="spin"></span>Analyze</button>
        <button class="btn ghost" onclick="clearAll()">Clear</button>
    </div>
</div>

<div id="results" class="hidden">
    <div class="card">
        <h2>Summary</h2>
        <div class="summary">
            <div class="maj-block">
                <span class="badge" id="maj-badge">—</span>
                <div class="maj-pct" id="maj-pct">–</div>
                <div class="maj-sub" id="maj-sub">of sentences are this sentiment</div>
                <div class="count-pills" id="count-pills"></div>
            </div>
            <div class="donut-box">
                <div class="donut-wrap">
                    <div class="donut" id="donut"></div>
                    <div class="donut-hole">
                        <span class="lbl" id="donut-lbl">overall</span>
                        <span class="val" id="donut-val">–</span>
                    </div>
                </div>
                <div class="legend" id="legend"></div>
            </div>
        </div>
        <div style="margin-top:16px">
            <div class="dist-label"><span>Sentiment distribution</span><span id="dist-count"></span></div>
            <div class="dist-bar" id="dist-bar"></div>
        </div>
    </div>

    <div class="card">
        <h2>Sentence breakdown <span id="breakdown-count" style="color:var(--muted);font-weight:400;font-size:13px"></span></h2>
        <div id="sent-list"></div>
    </div>
</div>

<footer>
    FiliSenti · served by <code>app.py</code> (Flask + ONNX Runtime) · API: <code>POST /api {"text":"…"}</code>
</footer>
</div>

<script>
const SENT = {
    Positive: { color: '#10B981', bg: 'rgba(16,185,129,.12)' },
    Neutral:  { color: '#F59E0B', bg: 'rgba(245,158,11,.12)' },
    Negative: { color: '#EF4444', bg: 'rgba(239,68,68,.12)' },
};
const EXAMPLES = [
    "Ang ganda ng serbisyo niyo! Sulit na sulit! Sobrang saya ko.",
    "Wala na talaga, ayaw ko na dito. Ang sama ng ugali. Hindi na ako babalik.",
    "Ang ganda ng lugar pero mahal naman. Okay lang naman, pwede na.",
];

const textEl = document.getElementById('text');
const countEl = document.getElementById('count');

textEl.addEventListener('input', () => {
    const t = textEl.value;
    countEl.textContent = t.length + ' characters';
    document.getElementById('error-box').classList.add('hidden');
});

function useExample(i) {
    textEl.value = EXAMPLES[i];
    textEl.dispatchEvent(new Event('input'));
}

function clearAll() {
    textEl.value = '';
    textEl.dispatchEvent(new Event('input'));
    document.getElementById('results').classList.add('hidden');
}

async function analyze() {
    const text = textEl.value.trim();
    const errorBox = document.getElementById('error-box');
    errorBox.classList.add('hidden');
    if (!text) { showError('Please enter some text first.'); return; }

    const btn = document.getElementById('analyze-btn');
    btn.disabled = true;
    document.getElementById('spin').style.display = 'inline-block';

    try {
        const res = await fetch('/api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Server error');
        render(data);
    } catch (e) {
        showError(e.message);
    } finally {
        btn.disabled = false;
        document.getElementById('spin').style.display = 'none';
    }
}

function showError(msg) {
    const el = document.getElementById('error-box');
    el.textContent = msg;
    el.classList.remove('hidden');
}

function donutGradient(pcts) {
    const stops = [];
    let start = 0;
    for (const n of Object.keys(SENT)) {
        const p = pcts[n];
        if (p <= 0) continue;
        stops.push(`${SENT[n].color} ${start.toFixed(2)}% ${(start + p).toFixed(2)}%`);
        start += p;
    }
    return 'conic-gradient(' + stops.join(', ') + ')';
}

function render(data) {
    const maj = data.majority;
    const m = SENT[maj];
    const res = document.getElementById('results');

    const badge = document.getElementById('maj-badge');
    badge.textContent = maj;
    badge.style.color = m.color;
    badge.style.background = m.bg;

    const pct = Math.round(data.percentages[maj]);
    document.getElementById('maj-pct').textContent = pct + '%';
    document.getElementById('maj-sub').textContent = pct + '% of ' + data.total + ' sentence' + (data.total === 1 ? '' : 's');
    document.getElementById('donut-val').textContent = maj;
    document.getElementById('donut-lbl').textContent = pct + '%';

    document.getElementById('count-pills').innerHTML = Object.keys(SENT).map(n =>
        `<span class="count-pill" style="color:${SENT[n].color};background:${SENT[n].bg}">${n} ${data.counts[n]}</span>`
    ).join('');

    document.getElementById('donut').style.background = donutGradient(data.percentages);

    document.getElementById('legend').innerHTML = Object.keys(SENT).map(n =>
        `<div class="row"><span class="dot" style="background:${SENT[n].color}"></span><span>${n}</span><span class="pct">${data.percentages[n].toFixed(1)}%</span></div>`
    ).join('');

    document.getElementById('dist-bar').innerHTML = Object.keys(SENT).filter(n => data.percentages[n] > 0).map(n =>
        `<div style="width:${data.percentages[n].toFixed(1)}%;background:${SENT[n].color}" title="${n} ${data.percentages[n].toFixed(1)}%"></div>`
    ).join('');
    document.getElementById('dist-count').textContent = data.total + ' sentence' + (data.total === 1 ? '' : 's');

    const list = document.getElementById('sent-list');
    list.innerHTML = '';
    data.sentences.forEach((s, i) => {
        const c = SENT[s.label];
        const el = document.createElement('div');
        el.className = 'sent';
        el.style.animationDelay = (i * 0.05) + 's';
        const scores = Object.keys(SENT).map(n =>
            `<span style="color:${SENT[n].color}">${n} ${(s.scores[n] * 100).toFixed(0)}%</span>`
        ).join('');
        el.innerHTML = `
            <div class="sent-top">
                <span class="badge" style="color:${c.color};background:${c.bg}">${s.label}</span>
                <span class="conf" style="color:${c.color}">${(s.confidence * 100).toFixed(1)}%</span>
            </div>
            <p class="sent-text"></p>
            <div class="bar"><div style="width:${Math.round(s.confidence * 100)}%;background:${c.color}"></div></div>
            <div class="scores-line">${scores}</div>
        `;
        el.querySelector('.sent-text').textContent = s.text;
        list.appendChild(el);
    });
    document.getElementById('breakdown-count').textContent = '(' + data.total + ')';

    res.classList.remove('hidden');
    res.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* theme */
const savedTheme = localStorage.getItem('filisenti-theme');
if (savedTheme) document.documentElement.dataset.theme = savedTheme;
function toggleTheme() {
    const cur = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = cur;
    localStorage.setItem('filisenti-theme', cur);
}
</script>
</body>
</html>
"""


@app.route("/logo.png")
def logo():
    return send_from_directory(LOGO_DIR, "logo.png")


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template_string(HTML)


@app.route("/api", methods=["POST"])
def api():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    if not text.strip():
        return jsonify({"error": "empty text"}), 400
    return jsonify(analyze(text))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
