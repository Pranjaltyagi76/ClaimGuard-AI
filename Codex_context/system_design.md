# System Design

## Data flow

```
dataset/claims.csv ──► generate_output.py ──► for each claim:
   ├─ extract_claim(text)                 (Claim Agent)
   ├─ for each image: analyze_image(img)  (Vision Agent, cached)
   ├─ check_evidence_standard(...)        (Evidence Agent)
   ├─ analyze_user_risk(row + history)    (Risk Agent)
   └─ decide(...)                         (Decision Agent)
        │
        ├─► output.csv          (spec: 14 columns, submission)
        └─► code/output.csv      (enriched: +confidence/fraud/explanation)
                                   consumed by ui_app.py (Streamlit)
```

## Runtime topology

- **Batch mode** (`generate_output.py`): processes the whole dataset offline,
  writes CSVs. This is where model calls happen.
- **Serve mode** (`ui_app.py` on Streamlit Cloud): reads the precomputed
  `code/output.csv` + committed images. **No API key needed at runtime**, so the
  live demo is cheap, fast, and can't fail on quota.

This split (offline inference, static serving) is deliberate: the expensive part
runs once; the public URL is a read-only view.

## Caching

`vision_agent.py` writes each image's JSON result to `code/cache/<image>.json`.

- Re-runs during prompt tuning cost **zero** additional calls.
- Duplicate images across claims are analyzed once.
- Cache is keyed by the sanitized image path.

## Cost & latency model

| Metric | Per image | Full test set (~82 images) |
| --- | --- | --- |
| Model calls | 1 | ~82 |
| Input tokens | ~1,000 | ~82,000 |
| Output tokens | ~80 | ~6,560 |
| Cost (Gemini 1.5 Flash) | — | **≈ $0.008** |
| Wall-clock (sequential) | ~1–3 s | ~2–4 min |

Cost is negligible; the binding constraint is **RPM/TPM rate limits**.

## Scaling strategy

1. **Caching** (done) — avoid repeat calls.
2. **Bounded concurrency** — a worker pool sized to the RPM limit.
3. **Exponential-backoff retry** on HTTP 429.
4. **Deterministic stages stay CPU-cheap** — they never bottleneck.

## Reliability

- Missing/unreadable image → `valid_image=false` → `not_enough_information`.
- API/parse failure → honest `unknown` fallback (no fabricated verdict).
- All non-vision logic is pure functions → trivially unit-testable.

## Tech stack

Python · Google Gemini (google-generativeai) · Pandas/NumPy · Pillow ·
Streamlit · python-dotenv.
