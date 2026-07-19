# Problems Faced (Bugs, Root Causes & Fixes)

An honest engineering log. Several of these were subtle and only surfaced when
inspecting the actual output, not the code.

## 1. Vision agent silently fabricated results 🔴 (most important)

**Symptom:** every single row in `output.csv` had `issue_type` from vision =
`broken_part`, `severity=medium`. Valid `crack`/`scratch` claims were all marked
`contradicted`.

**Root cause:** the Gemini call was failing (likely an unavailable model name),
and the `except` block returned a hard-coded
`{issue_type: "broken_part", severity: "medium", damage_visible: true}`
fallback. So "vision" never actually ran — every verdict was computed against a
constant.

**Fix:** use a valid, env-configurable model (`gemini-1.5-flash`), request JSON
output at `temperature=0`, and make the fallback **honest** — return
`unknown` / `valid_image=false` so the claim safely becomes
`not_enough_information` instead of a fabricated verdict.

## 2. `"port"` matched inside `"Support:"` 🐛

**Symptom:** a car body claim came out with `object_part = "port"`.

**Root cause:** object-part detection used substring matching (`"port" in text`),
and the transcript contains `"Support:"` on every agent turn.

**Fix:** whole-word matching with `\b` boundaries.

## 3. Agent-mentioned parts leaked into the claim 🐛

**Symptom:** a side-mirror claim resolved to `object_part = "door"` because the
support agent asked "Door ya bumper damage bhi hai?".

**Root cause:** the parser read the whole transcript, including the agent's
questions.

**Fix:** parse **only the customer's turns** before extracting issue/part.

## 4. `requirements.txt` pinned to non-existent versions 🔴 (deploy blocker)

**Symptom:** would have broken the Streamlit Cloud build.

**Root cause:** pins like `pandas==3.0.2`, `numpy==2.4.4`, `streamlit==1.57.0`
don't exist on PyPI.

**Fix:** repin to real, wheel-available versions.

## 5. Output schema didn't match the spec 🐛

**Symptom:** `output.csv` was missing `supporting_image_ids`, had extra columns,
and wrong column order.

**Fix:** emit exactly the 14 required columns, in order, and derive
`supporting_image_ids` from the images where damage was detected.

## 6. Invalid `risk_flags` vocabulary 🐛

**Symptom:** flags like `uncertain_claim`, `low_risk` — none in the allowed list.

**Fix:** map to the spec's allowed vocabulary and add real detectors
(prompt-injection → `text_instruction_present` + `manual_review_required`).

## 7. Only the first image was analyzed 🐛

**Root cause:** `get_first_image()` ignored multi-image evidence, making
`supporting_image_ids` meaningless.

**Fix:** analyze **all** images per claim and pick the one(s) showing damage.

## 8. Unknown vision → false "contradicted" 🐛

**Fix:** the Decision Agent now returns `not_enough_information` when the image
is invalid or shows no clear damage, instead of a false contradiction.

## Lessons

- **Inspect the outputs, not just the code.** The `broken_part` monotony was
  invisible in the code but obvious in the CSV.
- **Fallbacks must fail honestly.** A "graceful" fallback that invents data is
  worse than an error.
- **String matching needs boundaries and speaker awareness** in conversational
  data.
