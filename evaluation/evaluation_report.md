# ClaimGuard AI — Evaluation & Operational Analysis

This report covers correctness evaluation on the labeled sample set and an
operational analysis (model calls, tokens, cost, latency, and rate-limit
strategy) for processing the full test set.

---

## 1. How to evaluate

The labeled examples in `dataset/sample_claims.csv` carry the expected
`claim_status`. Run:

```bash
cd code
python main.py          # runs the pipeline on the sample set and prints accuracy
```

`main.py` compares predicted `claim_status` against the labeled value and
reports accuracy. Use it to tune prompts/thresholds before generating the final
`output.csv` for `dataset/claims.csv` via `python generate_output.py`.

---

## 2. Which stages call the model

| Stage | Type | Model call? |
|---|---|---|
| Claim Agent (parse the transcript) | Deterministic NLP | No |
| Vision Agent (inspect each image) | **Gemini vision** | **Yes — 1 call/image** |
| Evidence Agent (sufficiency) | Deterministic rules | No |
| Risk Agent (fraud/injection/history) | Deterministic rules | No |
| Decision Agent (final verdict) | Deterministic rules | No |

**Design choice:** only the Vision Agent needs a multimodal model. Claim
parsing, evidence checks, risk scoring, and the final decision are deterministic
so they are free, instant, reproducible, and auditable. This keeps cost and
latency proportional to the number of *images*, not the number of *stages*.

---

## 3. Volume (current test set)

- Claims processed: **44**
- Images processed: **82** (1–3 per claim)
- Model calls: **82** vision calls (1 per image) + **0** text calls
- Verdict mix: 28 supported / 16 contradicted

---

## 4. Token & cost estimate

Pricing assumption: **Gemini 1.5 Flash**, approx. **$0.075 / 1M input tokens**
and **$0.30 / 1M output tokens** (image input billed as tokens by resolution).

Per image (approx.):

- Prompt text: ~250 input tokens
- Image: ~250–1,000 input tokens (single tile, default resolution)
- JSON output: ~80 output tokens

| Metric | Per image | Full test set (82 images) |
|---|---|---|
| Input tokens | ~1,000 | ~82,000 |
| Output tokens | ~80 | ~6,560 |
| Input cost | — | ~$0.0062 |
| Output cost | — | ~$0.0020 |
| **Total** | — | **≈ $0.008 (well under 1 cent)** |

Even at 10× the volume this stays under $0.10, so cost is not the binding
constraint — rate limits and latency are.

---

## 5. Latency & runtime

- Per vision call: ~1–3 s (Flash tier).
- Sequential runtime for 82 images: ~2–4 minutes.
- The dominant cost is network round-trips, not local compute.

---

## 6. Rate limits (TPM/RPM) & mitigation strategy

Gemini Flash free/standard tiers cap requests-per-minute and tokens-per-minute.
82 images can exceed a low RPM cap if fired in a tight loop.

Strategies used / available in this codebase:

1. **Caching (implemented).** `vision_agent.py` writes each image's JSON result
   to `code/cache/`. Re-runs (and repeated images) cost **zero** additional
   calls — critical during iterative prompt tuning.
2. **Deterministic non-vision stages (implemented).** 4 of 5 agents make no
   model calls, so only images consume quota.
3. **Honest failure (implemented).** On any API/parse error the Vision Agent
   returns `unknown`/`valid_image=false` instead of fabricating a result, so a
   throttled call degrades to `not_enough_information` rather than a wrong
   verdict.
4. **Throttle / retry (recommended for scale).** Add a small sleep between calls
   and exponential-backoff retry on 429s to stay under RPM. For large batches,
   process concurrently with a bounded worker pool sized to the RPM limit.

---

## 7. Known limitations (honest)

- The Claim Agent uses rule-based keyword extraction (fast, deterministic) — it
  can miss unusual phrasings; the Roadmap proposes an LLM-based extractor.
- Severity and object-part cross-checks rely on the vision model's labels.
- `supporting_image_ids` currently picks the image(s) where damage was detected;
  multi-image evidence fusion is a roadmap item.
