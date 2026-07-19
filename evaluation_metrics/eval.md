# Evaluation Methodology (`eval.md`)

This folder covers **quality metrics** — how *correct* the predictions are.
For **operational** analysis (cost, tokens, latency, rate limits) see
[`../evaluation/evaluation_report.md`](../evaluation/evaluation_report.md).

## What we evaluate

The primary label is **`claim_status`** ∈ {`supported`, `contradicted`,
`not_enough_information`}. Secondary signals we can score when labels exist:

- `evidence_standard_met` (boolean sufficiency)
- `issue_type` and `object_part` (exact-match against allowed vocab)
- `risk_flags` (detection of injection / history risk)

## Data

`dataset/sample_claims.csv` is the **labeled** set — it contains the expected
`claim_status` for each row. We evaluate against it *before* generating final
predictions for the unlabeled `dataset/claims.csv`.

## Metrics defined

| Metric | Meaning | Why it matters here |
| --- | --- | --- |
| **Accuracy** | fraction of claims with correct `claim_status` | headline correctness |
| **Per-class Precision** | of claims we called *X*, how many were *X* | false-approval control |
| **Per-class Recall** | of true *X* claims, how many we caught | fraud-catch rate |
| **Per-class F1** | harmonic mean of P and R | balanced per-class view |
| **Macro-F1** | unweighted mean F1 across classes | treats rare classes fairly |
| **Confusion matrix** | full breakdown of pred vs true | shows *where* it fails |

### The metric that matters most

For a system near money, the costliest error is a **false `supported`** on a
fraudulent claim. So we watch **precision of `supported`** and **recall of
`contradicted`** especially closely — and the design deliberately routes
uncertainty to `not_enough_information` (manual review) rather than guessing
`supported`.

## How to run

```bash
cd code
python generate_output.py            # produce predictions (needs a Gemini key)

cd ../evaluation_metrics
python metrics.py \
  --gold ../dataset/sample_claims.csv \
  --pred ../code/output.csv \
  --column claim_status
```

`metrics.py` prints accuracy, a confusion matrix, and per-class P/R/F1, and
writes a machine-readable `results.json`. It joins predictions to gold on
`(user_id, image_paths)`, falling back to row order.

## Honest status

Final numbers require running the harness against the labeled sample set with a
working `GEMINI_API_KEY`. Because the earlier vision run failed silently (see
[`../Codex_context/problems_faced.md`](../Codex_context/problems_faced.md)),
current committed predictions are **not** a valid basis for reporting accuracy —
re-run vision first, then compute metrics. No numbers are hard-coded in this
folder.
