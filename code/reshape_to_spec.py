"""One-off utility (stdlib only).

Rebuilds two things from the existing enriched code/output.csv:

1. ../dataset/claims.csv  -> the input file the batch pipeline reads
   (reconstructed so `python generate_output.py` is runnable again).

2. ../output.csv          -> a spec-compliant submission file with the exact
   14 columns in order, normalized object parts, allowed risk-flag values,
   prompt-injection detection, and supporting_image_ids.

NOTE: This reshapes an existing run. For real, fresh vision results, set a
working GEMINI_API_KEY in a .env file and run `python generate_output.py`.
"""

import csv
import os
import re

SRC = "output.csv"                     # enriched file in code/
CLAIMS_OUT = "../dataset/claims.csv"
SPEC_OUT = "../output.csv"

SPEC_COLUMNS = [
    "user_id", "image_paths", "user_claim", "claim_object",
    "evidence_standard_met", "evidence_standard_met_reason", "risk_flags",
    "issue_type", "object_part", "claim_status", "claim_status_justification",
    "supporting_image_ids", "valid_image", "severity",
]

ALLOWED_PARTS = {
    "car": {"front_bumper", "rear_bumper", "door", "hood", "windshield",
            "side_mirror", "headlight", "taillight", "fender", "quarter_panel",
            "body", "unknown"},
    "laptop": {"screen", "keyboard", "trackpad", "hinge", "lid", "corner",
               "port", "base", "body", "unknown"},
    "package": {"box", "package_corner", "package_side", "seal", "label",
                "contents", "item", "unknown"},
}

INJECTION_PATTERNS = [
    r"ignore .*instruction", r"approve .*(immediately|claim|quickly)",
    r"mark .*(supported|approved)", r"skip .*(manual )?review",
    r"follow .*note", r"the note is enough",
]


def to_bool_str(v):
    return "true" if str(v).strip().lower() in ("true", "1", "yes") else "false"


def norm_part(part, claim_object):
    p = (part or "unknown").strip().lower().replace(" ", "_")
    return p if p in ALLOWED_PARTS.get(claim_object, set()) else "unknown"


def risk_flags_for(claim_text):
    flags = []
    t = str(claim_text).lower()
    if any(re.search(p, t) for p in INJECTION_PATTERNS):
        flags += ["text_instruction_present", "manual_review_required"]
    if "original photo" in t or "own laptop" in t:
        flags.append("non_original_image")
    return ";".join(dict.fromkeys(flags)) if flags else "none"


def first_image_id(image_paths):
    first = str(image_paths).split(";")[0].strip()
    return os.path.splitext(os.path.basename(first))[0]


def main():
    with open(SRC, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # 1) Reconstruct claims.csv (input schema)
    with open(CLAIMS_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["user_id", "image_paths", "user_claim", "claim_object"]
        )
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in
                        ["user_id", "image_paths", "user_claim", "claim_object"]})

    # 2) Spec-compliant output.csv
    with open(SPEC_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SPEC_COLUMNS)
        w.writeheader()
        for r in rows:
            obj = str(r["claim_object"]).strip().lower()
            status = r["claim_status"]
            supporting = (first_image_id(r["image_paths"])
                          if status in ("supported", "contradicted") else "none")
            w.writerow({
                "user_id": r["user_id"],
                "image_paths": r["image_paths"],
                "user_claim": r["user_claim"],
                "claim_object": obj,
                "evidence_standard_met": to_bool_str(r["evidence_standard_met"]),
                "evidence_standard_met_reason": r["evidence_standard_met_reason"],
                "risk_flags": risk_flags_for(r["user_claim"]),
                "issue_type": r["issue_type"],
                "object_part": norm_part(r["object_part"], obj),
                "claim_status": status,
                "claim_status_justification": r.get("ai_explanation", r["claim_status_justification"]),
                "supporting_image_ids": supporting,
                "valid_image": to_bool_str(r["valid_image"]),
                "severity": r["severity"],
            })

    print(f"Wrote {CLAIMS_OUT} and {SPEC_OUT} ({len(rows)} rows).")


if __name__ == "__main__":
    main()
