# How Codex Helped Me Deliver ClaimGuard AI

> A phase-by-phase account of building ClaimGuard AI with Codex as my
> pair-programming partner. Every technical detail below is verifiable in this
> repository — the agents, the fixes, the docs, and the evaluation harness.

I didn't want to use an AI assistant as a copy-paste machine. I wanted a
**partner** — something I could think out loud with, that would push back on bad
ideas, catch my mistakes, and help me move from a rough concept to a deployed
product. Here's how that partnership played out across the project.

---

## Phase 0 — From an idea to an architecture 🧠

**What I was doing:** turning a real problem (insurance-photo fraud at a phone
showroom in Ghaziabad — see [motivation.md](Codex_context/motivation.md)) into a
system design.

**How Codex partnered with me:**
- We brainstormed *decomposition*: instead of one giant prompt, break the
  decision into cooperating agents (Claim → Vision → Evidence → Risk → Decision).
- Codex helped me pressure-test the design — e.g. the decision that **only the
  Vision Agent needs a model call**, so cost scales with images, not steps.
- We defined the **data contracts** between agents (plain dicts with fixed keys)
  so each stage stayed independently testable.

**Outcome:** the architecture in
[architecture_design.md](Codex_context/architecture_design.md).

---

## Phase 1 — Implementation 🛠️

**What I was doing:** building the five agents, the Gemini vision integration,
and the batch pipeline.

**How Codex partnered with me:**
- Scaffolding each agent quickly so I could focus on the logic, not boilerplate.
- Writing the **Gemini vision prompt** with a strict JSON output schema and the
  allowed-value lists from the problem statement.
- Adding **per-image caching** so re-runs during prompt tuning cost nothing —
  Codex suggested keying the cache by sanitized image path.
- Wiring `generate_output.py` to produce the required output columns.

**Outcome:** a working end-to-end pipeline and a Streamlit dashboard.

---

## Phase 2 — Hardening & debugging 🔍 (where a partner really matters)

This is the phase where having a second set of eyes changed the result. I
learned to **inspect the outputs, not just the code** — and that surfaced real
bugs (all documented in
[problems_faced.md](Codex_context/problems_faced.md)):

- **The silent vision fallback** — every row was coming back as `broken_part`
  because a failing model call fell through to a hard-coded fallback. The fix:
  make the fallback **honest** (`unknown` → `not_enough_information`) instead of
  fabricating a verdict.
- **`"port"` matching inside `"Support:"`** — switched to word-boundary matching.
- **Agent-mentioned parts leaking in** — parse only the *customer's* turns.
- **Dependency pins that didn't exist** — would have broken the deploy build.
- **Output schema drift** — aligned to the exact 14-column spec and added
  `supporting_image_ids`.
- **Prompt-injection in the claim text** — added explicit detection
  (`text_instruction_present` + manual review).

**Outcome:** a system that is honest about its own uncertainty and safe near
money.

---

## Phase 3 — Evaluation, security & deployment 🚀

**What I was doing:** proving the system works and shipping a live URL.

**How Codex partnered with me:**
- Built the **operational analysis** (cost, tokens, latency, rate limits) in
  [evaluation/evaluation_report.md](evaluation/evaluation_report.md).
- Built a **runnable metrics harness**
  ([evaluation_metrics/metrics.py](evaluation_metrics/metrics.py)) — accuracy,
  confusion matrix, per-class precision/recall/F1 — and I made a point of **not
  hard-coding any numbers**, so results are computed from real labeled data.
- Wrote a **security review**
  ([security_review.md](Codex_context/security_review.md)) covering prompt
  injection, secret management, and data privacy.
- Planned the **deployment** (Streamlit Community Cloud, offline-inference /
  static-serving split) so the live demo needs no runtime API key.

**Outcome:** a public repo with full documentation and a deployable app.

---

## How I actually worked with my AI partner

1. **I drove, it advised.** I made the design and product calls; it accelerated
   and challenged them.
2. **Small, verifiable steps.** Every change was something I could run and check.
3. **Output-first debugging.** The biggest bug was invisible in the code and
   obvious in the CSV — so we always looked at real outputs.
4. **Honesty over polish.** When something wasn't measured, we said so rather
   than inventing a number.

---

## What I took away

The most valuable thing wasn't the code an AI can generate — it's the
**discipline** a good partner reinforces: decompose the problem, fail honestly,
inspect real outputs, and build something you can actually deploy and defend.
ClaimGuard AI is a system I understand end to end, and I can explain every line
and every decision in it.

— **Pranjal Tyagi**
