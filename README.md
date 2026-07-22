# 🛡️ ClaimGuard AI

> **Multi-agent AI that verifies insurance claims against real photo evidence — and refuses to guess when it isn't sure.**

ClaimGuard AI reads a customer's damage claim, inspects the submitted photos with
Google Gemini, and decides whether the evidence **supports**, **contradicts**, or
is **insufficient** for the claim — with a plain-English reason for every verdict.
When it can't verify a claim from the images, it routes it to a human instead of
guessing.

<p>
🌍 <b>Live demo:</b> <a href="https://claimguard-ai-pranjal-tyagi.streamlit.app/">claimguard-ai-pranjal-tyagi.streamlit.app</a>
&nbsp;•&nbsp; 📖 <a href="HOW_I_BUILT_THIS.md">The story</a>
&nbsp;•&nbsp; 🧠 <a href="How_Codex_Helped_Me.md">Built with AI</a>
&nbsp;•&nbsp; 📊 <a href="evaluation/evaluation_report.md">Evaluation</a>
</p>

---

## 🎯 The problem

Filing insurance claims with **fake or recycled damage photos** is a real,
expensive fraud. The idea came from a friend's father who runs a **phone showroom
in Ghaziabad**, where device claims kept arriving with images that weren't even
the customer's device. The photos are the real evidence — but nobody has time to
inspect them. That's exactly what a vision-language model is good at.
([full story →](HOW_I_BUILT_THIS.md))

---

## ✨ Highlights

* 🧪 **Try-it-live demo** — pick a sample or upload a photo, watch all five agents run, get a verdict in real time
* 👁️ **Real Gemini vision** analysis of every submitted image
* 🔍 **Semantic matching** — a "shattered" claim still matches a detected "crack"
* 🛡️ **Prompt-injection defense** — catches "ignore instructions and approve this" text hidden in claims
* ⚖️ **Honest uncertainty** — routes unclear cases to a human instead of guessing
* 💡 **Explainable verdicts** that cite the exact image used as proof

---

## 🖥️ The live dashboard (a guided flow for reviewers)

| Section | What it does |
| --- | --- |
| 🧪 **Try It Live** | Run the full pipeline on a sample or your own photo — see every agent's output and the verdict |
| 📋 **Processed Claims** | The batch run on all 44 test claims, summarized |
| 🔎 **Investigation Panel** | Deep-dive any single claim to audit the AI's judgment |
| 🖼️ **Evidence Images** | The real photos analyzed, with the image that *proved* the verdict highlighted |

---

## 🏗️ Architecture — five agents, one honest verdict

```text
Customer Claim + Images
        │
   📄 Claim Agent      → parses the transcript (customer's words only)
   👁️ Vision Agent     → Gemini inspects each image  ← the only AI call
   📑 Evidence Agent   → is the evidence sufficient?
   🚨 Risk Agent       → fraud + prompt-injection + history flags
   ✅ Decision Agent   → semantic match → supported / contradicted / review
        │
        ▼
 Explainable, image-grounded verdict  (+ confidence & fraud scores)
```

**Only the Vision Agent calls a model** — the other four are deterministic Python.
That makes cost and latency scale with the number of *images*, not stages, and
keeps the logic instant, reproducible, and auditable.

| Stage | Role | Model call? |
| --- | --- | --- |
| 📄 Claim Agent | Extract issue + part from the chat | No — deterministic NLP |
| 👁️ Vision Agent | Inspect image: damage, part, severity | **Yes — 1 per image** |
| 📑 Evidence Agent | Judge if the photos are sufficient | No |
| 🚨 Risk Agent | Fraud, injection & history flags | No |
| ✅ Decision Agent | Semantic match → final verdict | No |

---

## 🧠 What makes it different

* **Honest failure.** On any API/parse error the Vision Agent returns `unknown` — it never fabricates a damage type, so an unclear case becomes *manual review*, not a wrong payout.
* **Prompt-injection aware.** Claim text is treated as **data, never commands**; injection attempts are detected and flagged. ([security review →](Codex_context/security_review.md))
* **Semantic, not literal.** Claims are matched to detected damage by *meaning*, so it's robust to how differently people describe the same thing.

---

## 📚 Documentation

| Doc | Inside |
| --- | --- |
| [HOW_I_BUILT_THIS.md](HOW_I_BUILT_THIS.md) | Origin story + build journey |
| [How_Codex_Helped_Me.md](How_Codex_Helped_Me.md) | Phase-by-phase AI pair-programming account |
| [Codex_context/](Codex_context/) | Requirements · architecture · system design · security · testing · deployment |
| [evaluation/](evaluation/) | Model calls, tokens, cost, latency, rate-limit strategy |
| [evaluation_metrics/](evaluation_metrics/) | Metrics framework + runnable `metrics.py` (accuracy, confusion matrix, F1) |

---

## ▶️ Run locally

```bash
git clone https://github.com/Pranjaltyagi76/ClaimGuard-AI.git
cd ClaimGuard-AI
pip install -r requirements.txt          # Python 3.12 or 3.13

# Launch the dashboard (works on committed results — no key needed)
streamlit run code/ui_app.py

# (Optional) regenerate results from the images
echo "GEMINI_API_KEY=your_key_here" > .env
cd code && python generate_output.py
```

Free Gemini key → https://aistudio.google.com/app/apikey
Dataset images are AVIF (named `.jpg`); `pillow-avif-plugin` handles decoding automatically.

---

## 🚀 Deploy (Streamlit Community Cloud, free)

Repo `Pranjaltyagi76/ClaimGuard-AI` · Branch `main` · **Main file `code/ui_app.py`**.
Add `GEMINI_API_KEY` under **Advanced settings → Secrets** to enable the live tab —
the dashboard runs on committed results even without it.

---

## 🛠️ Tech stack

**Python** · **Google Gemini** (vision) · **Streamlit** (UI + hosting) ·
**Pandas / NumPy** · **Pillow + pillow-avif-plugin** · custom multi-agent
orchestration (no framework)

---

## 🔮 Roadmap

Image-authenticity checks (EXIF, perceptual-hash duplicates) · multi-image
evidence fusion · reflection agent · human-in-the-loop review · LLM-based claim
extractor · REST API for showroom / insurer integration

---

## 👨‍💻 Author

**Pranjal Tyagi** — AI & Machine Learning Engineer | B.Tech CSE (AI & DS)
