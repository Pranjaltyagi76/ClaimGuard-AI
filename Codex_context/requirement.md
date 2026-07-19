# Requirements

## For whom are we building?

| Stakeholder | Need |
| --- | --- |
| Device retailer / showroom owner | Screen incoming damage claims for obvious fraud before payout |
| Insurer / TPA claim team | Auto-triage claims into supported / contradicted / needs-review |
| Claim reviewer (human) | A prioritized queue with reasons and supporting image IDs |
| Honest customer | Fast approval when the evidence clearly supports the claim |

## Scope

Each claim concerns exactly one object: **`car`**, **`laptop`**, or
**`package`**. The system decides whether the submitted images **support**,
**contradict**, or provide **not enough information** for the customer's claim.

## Functional requirements

1. Extract the actual damage claim from a multi-turn customer conversation.
2. Inspect one or more submitted images and identify the visible issue type,
   object part, and severity.
3. Decide whether the image evidence is *sufficient* to evaluate the claim.
4. Produce a final status: `supported` / `contradicted` / `not_enough_information`.
5. Select the **image IDs** that support the decision.
6. Flag risks: image quality, claim mismatch, authenticity, user-history, and
   **prompt-injection** text inside the claim.
7. Produce short, image-grounded justifications.

## Input schema (`dataset/claims.csv`)

`user_id`, `image_paths` (semicolon-separated), `user_claim` (chat transcript),
`claim_object`.

## Output schema (`output.csv`) — exact columns, in order

`user_id`, `image_paths`, `user_claim`, `claim_object`, `evidence_standard_met`,
`evidence_standard_met_reason`, `risk_flags`, `issue_type`, `object_part`,
`claim_status`, `claim_status_justification`, `supporting_image_ids`,
`valid_image`, `severity`.

## Controlled vocabularies

- `claim_status`: `supported` | `contradicted` | `not_enough_information`
- `issue_type`: dent, scratch, crack, glass_shatter, broken_part, missing_part,
  torn_packaging, crushed_packaging, water_damage, stain, none, unknown
- `severity`: none | low | medium | high | unknown
- `risk_flags`: none, blurry_image, cropped_or_obstructed, low_light_or_glare,
  wrong_angle, wrong_object, wrong_object_part, damage_not_visible,
  claim_mismatch, possible_manipulation, non_original_image,
  text_instruction_present, user_history_risk, manual_review_required
- `object_part`: per-object lists (car/laptop/package) as defined in the spec.

## Non-functional requirements

- **Cost:** processing the full test set must cost well under $0.10.
- **Latency:** batch of ~80 images completes in a few minutes.
- **Rate limits:** stay within Gemini Flash TPM/RPM via caching + honest failure.
- **Reproducibility:** identical inputs produce identical outputs (temperature 0,
  deterministic non-vision stages, per-image caching).
- **Deployability:** a public live URL that runs without a runtime API key
  (dashboard reads precomputed results).
