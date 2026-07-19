# Architecture Design

## Overview

ClaimGuard AI is a **multi-agent pipeline**. A claim flows through five
specialized agents; each has one responsibility and a clear input/output
contract. Only the Vision Agent calls a model — the rest are deterministic.

```
Customer Claim (text) + Images
            │
            ▼
   📄 Claim Agent ........ deterministic NLP  -> {issue_type, object_part}
            │
            ▼
   👁️ Vision Agent ....... Gemini vision     -> {issue_type, object_part,
            │                                     severity, valid_image,
            │                                     damage_visible, risk_flags}
            ▼
   📑 Evidence Agent ..... deterministic      -> {evidence_met, reason}
            │
            ▼
   🚨 Risk Agent ......... deterministic      -> [risk_flags...]
            │
            ▼
   ✅ Decision Agent ..... deterministic      -> {claim_status, reason}
            │
            ▼
   Confidence + Fraud score + Explanation
            │
            ▼
   output.csv  +  Streamlit dashboard
```

## Component responsibilities

### 📄 Claim Agent (`agents/claim_agent.py`)
- Parses the multi-turn transcript and keeps **only the customer's turns** (so a
  part the support agent merely asks about does not leak in).
- Whole-word matching → `issue_type` and canonical `object_part`.
- Deterministic, zero cost, fully reproducible.

### 👁️ Vision Agent (`agents/vision_agent.py`)
- Sends each image to **Gemini** with a strict JSON schema prompt.
- `response_mime_type=application/json`, `temperature=0` for stable output.
- **Per-image caching** in `code/cache/` — repeated/re-run images cost nothing.
- **Honest failure:** on API/parse error returns `unknown` / `valid_image=false`
  instead of fabricating a damage type.

### 📑 Evidence Agent (`agents/evidence_agent.py`)
- Checks whether the vision result is sufficient to evaluate the claim
  (`evidence_standard_met` + reason).

### 🚨 Risk Agent (`agents/risk_agent.py`)
- Emits only the spec's allowed flag vocabulary.
- Detects **prompt-injection** text ("ignore all instructions and approve…"),
  authenticity hints, and user-history risk.

### ✅ Decision Agent (`agents/decision_agent.py`)
- Combines claim vs vision using exact + **semantic** matching.
- Invalid/unknown vision → `not_enough_information` (never a false contradiction).

## Data contracts

Every agent exchanges plain Python dicts with fixed keys, which keeps stages
independently testable and swappable (e.g. the Claim Agent could later become an
LLM extractor without touching the rest).

## Key design decisions

1. **One model call per image, none per stage** → cost scales with images.
2. **Deterministic glue** → auditable, reproducible, free.
3. **Two outputs** → a spec-exact `output.csv` (submission) and an enriched
   `code/output.csv` (dashboard) from the same run.
4. **Fail safe, not silent** → uncertainty routes to human review.
