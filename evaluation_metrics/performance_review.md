# Performance Review (`performance_review.md`)

A structured review of how the system performs — correctness, behavioral
quality, efficiency, and where it breaks. Numbers that require labeled data are
marked as **[run `metrics.py` to fill]**; nothing here is fabricated.

## 1. Correctness (quality metrics)

Run against the labeled `dataset/sample_claims.csv`:

| Metric | Value |
| --- | --- |
| Accuracy (`claim_status`) | **[run `metrics.py`]** |
| Precision — `supported` | **[run]** |
| Recall — `contradicted` | **[run]** |
| Macro-F1 | **[run]** |

> Method and rationale in [`eval.md`](eval.md). The harness writes
> `results.json` you can paste here.

## 2. Behavioral quality (verified during development)

These are correctness properties of the deterministic logic, confirmed with
direct assertions (see [`../Codex_context/testing_strategy.md`](../Codex_context/testing_strategy.md)):

| Behavior | Status |
| --- | --- |
| Reads only the customer's turns (ignores agent questions) | ✅ verified |
| Word-boundary matching (`"port"` ≠ `"Support"`) | ✅ verified |
| Prompt-injection → `text_instruction_present` + review | ✅ verified |
| API/parse failure → honest `unknown`, no fabrication | ✅ verified |
| Invalid/unknown vision → `not_enough_information` | ✅ verified |
| Output conforms to the 14-column spec schema | ✅ verified |

## 3. Efficiency (measured / estimated)

| Metric | Value |
| --- | --- |
| Model calls | 1 per image (0 per non-vision stage) |
| Evidence images referenced | 82 (37 analyzed live; rest routed to manual review under the free-tier daily cap) |
| Est. cost (Gemini 2.5 Flash) | ≈ **$0.04** for the full 82 images |
| Latency per image | ~2–8 s (Flash tier) |
| Repeat-run cost (cached) | **$0** |

Details: [`../evaluation/evaluation_report.md`](../evaluation/evaluation_report.md).

## 4. Error analysis (how to read the confusion matrix)

When you run `metrics.py`, focus on:

- **`supported` predicted but true `contradicted`** — the dangerous cell
  (false approval of likely fraud). Should be near-zero.
- **`contradicted` predicted but true `supported`** — annoys honest customers;
  tune semantic matching / vision prompt if high.
- **Anything → `not_enough_information`** — acceptable "safe" errors; these route
  to a human rather than causing a wrong payout.

## 5. Strengths

- Honest uncertainty handling (fails to manual review, not to a wrong verdict).
- Cost/latency scale with images, not pipeline depth.
- Deterministic, reproducible, auditable non-vision stages.
- Explicit prompt-injection defense.

## 6. Weaknesses / next steps

- Claim extraction is keyword-based (misses unusual phrasing) → planned LLM
  extractor.
- Image authenticity only heuristically flagged → planned EXIF / perceptual-hash
  duplicate detection.
- Single-image decisioning → planned multi-image evidence fusion.
- No automated CI gate on schema/accuracy yet → planned `pytest` + schema lint.

## 7. Verdict

The system optimizes for the right objective: **minimize false approvals, prefer
human review when unsure.** Once `metrics.py` is run on the labeled set, this
review should be updated with the measured accuracy and confusion matrix.
