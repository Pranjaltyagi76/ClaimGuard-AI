# ClaimGuard AI — Evaluation & Operational Analysis

This report covers how to evaluate the system, and an operational analysis
(model calls, tokens, cost, latency, and rate-limit strategy) based on the
**actual run** used to produce `output.csv`.

---

## 1. How to evaluate

**Correctness (quality metrics):** the runnable harness in
[`../evaluation_metrics/metrics.py`](../evaluation_metrics/metrics.py) computes
accuracy, a confusion matrix, and per-class precision/recall/F1 against a
labeled file:

```bash
cd evaluation_metrics
python metrics.py --gold ../dataset/sample_claims.csv --pred ../code/output.csv --column claim_status
```

`code/main.py` also runs the pipeline on the labeled sample set and prints a
quick accuracy number for prompt/threshold tuning before generating the final
predictions with `python generate_output.py`.

No accuracy figure is hard-coded here — it is computed from real labeled data
when the harness is run.

---

## 2. Which stages call the model

| Stage | Type | Model call? |
|---|---|---|
| Claim Agent (parse the transcript) | Deterministic NLP | No |
| Vision Agent (inspect each image) | **Gemini vision** | **Yes — 1 call/image** |
| Evidence Agent (sufficiency) | Deterministic rules | No |
| Risk Agent (fraud/injection/history) | Deterministic rules | No |
| Decision Agent (final verdict) | Deterministic rules | No |

**Design choice:** only the Vision Agent needs a multimodal model. The other
four stages are deterministic — free, instant, reproducible, and auditable. Cost
and latency scale with the number of *images*, not the number of *stages*.

---

## 3. Volume (actual run)

- Claims processed: **44**
- Evidence images referenced: **82** (1–3 per claim)
- Images analyzed with live Gemini vision: **37**
- The remaining images were **honestly routed to manual review** rather than
  analyzed, because the free-tier **daily request quota** was reached during
  development (see §6). The system reports these as `not_enough_information`
  instead of guessing.

**Verdict mix (44 claims):**

| Verdict | Count |
|---|---|
| ✅ Supported | 13 |
| ❌ Contradicted | 6 |
| ⚠️ Not enough information (manual review) | 25 |

This distribution reflects the system's core principle: when it cannot verify a
claim from the images, it escalates to a human rather than approving or rejecting
on a guess.

---

## 4. Model

- **Vision model:** Gemini Flash tier (default `gemini-2.5-flash`, configurable
  via `GEMINI_MODEL`). Model availability on free-tier keys shifts over time —
  the code makes the model an env variable precisely so it can be swapped
  without code changes.
- **Text model calls:** none. Only images hit the API.

---

## 5. Token & cost estimate

Pricing assumption: **Gemini 2.5 Flash**, approx. **$0.30 / 1M input tokens**
and **$2.50 / 1M output tokens** (image input billed as tokens by resolution).

Per image (approx.): ~250 prompt tokens + ~250–1,000 image tokens input, ~80
tokens JSON output.

| Metric | Per image | Full set (82 images) |
|---|---|---|
| Input tokens | ~1,000 | ~82,000 |
| Output tokens | ~80 | ~6,560 |
| Input cost | — | ~$0.025 |
| Output cost | — | ~$0.016 |
| **Total** | — | **≈ $0.04 (a few cents)** |

Cost is negligible even at 10× the volume (< $0.50). **The binding constraint is
rate limits, not money.**

---

## 6. Rate limits & mitigation (the real bottleneck)

The free-tier key used has tight limits — in practice around **10 requests per
minute** and roughly **20 requests per day** for the Flash model. Processing 82
images in one sitting exceeds the daily cap, which is why part of the batch was
routed to manual review rather than analyzed.

Mitigations **implemented in the codebase**:

1. **Per-image caching (`code/cache/`).** Each image's JSON result is cached and
   committed, so re-runs and repeated images cost **zero** additional calls. The
   cache key is path-independent, so cached results work across machines and on
   the deployed app without any live call.
2. **Proactive throttle (`GEMINI_THROTTLE`).** A configurable delay between calls
   keeps the batch under the per-minute limit.
3. **Exponential-backoff retry (`GEMINI_MAX_RETRIES`).** Transient `429`s wait
   and retry (8s → 16s → 32s …) instead of failing.
4. **Fast-fail for the interactive UI.** The live demo sets retries to 1 and no
   throttle, so a rate-limited call returns immediately (to manual review)
   rather than hanging the interface.
5. **Honest failure.** On any API/parse error the Vision Agent returns
   `unknown` / `valid_image=false` — a throttled or failed call degrades to
   `not_enough_information`, never a fabricated verdict.
6. **Deterministic non-vision stages.** 4 of 5 agents make no model calls, so
   only images consume quota.

**For production scale:** a paid key removes the daily cap; the batch would then
run end-to-end in a few minutes using a bounded concurrent worker pool sized to
the account's RPM limit.

---

## 7. Latency & runtime

- Per vision call: ~2–8 s (Flash tier includes brief model "thinking" time).
- With throttling to respect the per-minute limit, the batch runs over several
  minutes; cached images are instant.
- The dominant cost is network round-trips and rate-limit waits, not local
  compute.

---

## 8. Known limitations (honest)

- Part of the batch is `not_enough_information` due to the free-tier daily cap,
  not model inability — a paid key analyzes every image.
- The Claim Agent uses deterministic keyword extraction; unusual phrasings can be
  missed (an LLM-based extractor is on the roadmap).
- Severity and object-part labels come from the vision model.
- `supporting_image_ids` picks the image(s) where damage was detected;
  multi-image evidence fusion is a roadmap item.
