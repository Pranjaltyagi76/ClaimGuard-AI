# Roadmap — How I Made This

## Timeline (honest)

**Phase 0 — Idea (earlier, out of curiosity).**
A conversation about insurance-photo fraud at a phone showroom in Ghaziabad
(see [motivation.md](motivation.md)) led me to sketch a **multi-agent
architecture** for image-grounded claim verification. At this stage it was
mostly design and a skeleton, not a hardened implementation.

**Phase 1 — Implementation (hackathon).**
When I found this hackathon — whose problem statement is *literally* multi-modal
evidence review for damage claims — I built out the real system:
- the five-agent pipeline,
- the Gemini vision integration with a strict JSON schema and caching,
- the decision + risk logic,
- a Streamlit dashboard.

**Phase 2 — Hardening & polish (hackathon).**
I inspected the actual outputs and fixed real bugs (see
[problems_faced.md](problems_faced.md)): the silent vision fallback, substring
matching, schema compliance, and the deploy-blocking dependency pins. I added an
evaluation report, security review, and deployment path.

**Phase 3 — Deploy.**
Public GitHub repo + live Streamlit URL that runs without a runtime API key.

## Build order (how the pieces came together)

1. Data contracts between agents (dicts with fixed keys).
2. Claim Agent (deterministic parsing) — cheap to test first.
3. Vision Agent + caching — the only model call.
4. Evidence, Risk, Decision agents.
5. `generate_output.py` batch runner → two CSVs.
6. Streamlit dashboard reading the enriched CSV.
7. Evaluation harness (`main.py`) on the labeled sample set.
8. Deployment + docs.

## Future roadmap

- **LLM-based Claim Agent** to replace keyword extraction for unusual phrasings.
- **Multi-image evidence fusion** (combine several photos into one judgment).
- **Reflection agent** that critiques the decision before finalizing.
- **User-history modeling** for stronger fraud priors.
- **Possible-manipulation detection** (EXIF, reverse-image, duplicate hashing).
- **Human-in-the-loop review UI** with accept/override + feedback capture.
- **REST API** for integration into a showroom/insurer workflow.
- **Temporal verification** (was this damage claimed before?).
