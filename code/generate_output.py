"""ClaimGuard AI - batch pipeline.

Reads dataset/claims.csv, runs the multi-agent pipeline on every claim, and
writes TWO files:

1. ../output.csv        -> spec-compliant submission (14 columns, exact order)
2. output.csv (here)    -> enriched view (adds confidence/fraud/explanation)
                           consumed by the Streamlit dashboard (ui_app.py)

Which stages use AI vs deterministic logic is documented in the README.
"""

import os
import pandas as pd

from agents.claim_agent import extract_claim
from agents.vision_agent import analyze_image
from agents.evidence_agent import check_evidence_standard
from agents.risk_agent import analyze_user_risk
from agents.decision_agent import decide

DATA_PATH = "../dataset/claims.csv"
HISTORY_PATH = "../dataset/user_history.csv"
IMAGE_BASE = "../dataset"

SPEC_OUTPUT_PATH = "../output.csv"        # submission artifact
UI_OUTPUT_PATH = "output.csv"             # dashboard artifact

# Required submission columns, in the exact order the problem statement asks for.
SPEC_COLUMNS = [
    "user_id",
    "image_paths",
    "user_claim",
    "claim_object",
    "evidence_standard_met",
    "evidence_standard_met_reason",
    "risk_flags",
    "issue_type",
    "object_part",
    "claim_status",
    "claim_status_justification",
    "supporting_image_ids",
    "valid_image",
    "severity",
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


# ---------------------------
# Helpers
# ---------------------------
def image_id_of(path):
    """Image ID = filename without extension, e.g. img_1."""
    base = os.path.basename(path.strip())
    return os.path.splitext(base)[0]


def get_image_list(image_paths):
    return [p.strip() for p in str(image_paths).split(";") if p.strip()]


def validate_part(part, claim_object):
    part = (part or "unknown").strip().lower().replace(" ", "_")
    allowed = ALLOWED_PARTS.get(claim_object, set())
    return part if part in allowed else "unknown"


def semantic_match(claim_issue, vision_issue):
    if not claim_issue or not vision_issue:
        return False, None
    if claim_issue == vision_issue:
        return True, claim_issue
    claim_tokens = set(claim_issue.lower().split("_"))
    vision_tokens = set(vision_issue.lower().split("_"))
    common = claim_tokens.intersection(vision_tokens)
    if common:
        return True, "_".join(sorted(common))
    return False, None


def compute_confidence(claim_issue, vision_issue, matched):
    if vision_issue in (None, "unknown"):
        return 0.50
    if claim_issue == vision_issue:
        return 0.95
    if matched:
        return 0.80
    return 0.25


def compute_fraud_score(claim_status, confidence, risk_flags):
    score = 0
    if claim_status == "contradicted":
        score += 70
    elif claim_status == "supported":
        score += 20
    else:
        score += 50
    score += (1 - confidence) * 30
    if "manual_review_required" in risk_flags:
        score += 10
    if "text_instruction_present" in risk_flags:
        score += 15
    return round(min(100, max(0, score)), 2)


def generate_explanation(claim_issue, vision_issue, status, confidence, ids):
    id_hint = f" (see image {', '.join(ids)})" if ids else ""
    if status == "supported":
        return (f"SUPPORTED: the image evidence shows '{vision_issue}', which "
                f"aligns with the claimed '{claim_issue}'{id_hint}. "
                f"Confidence {round(confidence * 100)}%.")
    if status == "contradicted":
        return (f"CONTRADICTED: the image evidence shows '{vision_issue}', which "
                f"does not match the claimed '{claim_issue}'{id_hint}.")
    return ("NOT ENOUGH INFORMATION: image evidence could not be conclusively "
            "analyzed; routed to manual review.")


# ---------------------------
# Main pipeline
# ---------------------------
def run_pipeline():
    df = pd.read_csv(DATA_PATH)

    history = None
    if os.path.exists(HISTORY_PATH):
        try:
            history = pd.read_csv(HISTORY_PATH).set_index("user_id")
        except Exception:
            history = None

    spec_rows = []
    ui_rows = []

    for _, row in df.iterrows():
        user_id = row["user_id"]
        claim_text = row["user_claim"]
        claim_object = str(row["claim_object"]).strip().lower()

        # ---- 1. Claim Agent (deterministic NLP) ----
        claim_info = extract_claim(claim_text)
        claim_issue = claim_info.get("issue_type")
        object_part = validate_part(claim_info.get("object_part"), claim_object)

        # ---- 2. Vision Agent (AI - Gemini) over ALL images ----
        image_rel_paths = get_image_list(row["image_paths"])
        best_vision = None
        supporting_ids = []

        for rel in image_rel_paths:
            full = os.path.join(IMAGE_BASE, rel)
            vinfo = analyze_image(full)
            if best_vision is None:
                best_vision = vinfo
            # Prefer an image that actually shows damage.
            if vinfo.get("damage_visible") and vinfo.get("valid_image"):
                best_vision = vinfo
                supporting_ids.append(image_id_of(rel))

        if best_vision is None:
            best_vision = {"valid_image": False, "issue_type": "unknown",
                           "severity": "unknown", "damage_visible": False}

        vision_issue = best_vision.get("issue_type", "unknown")
        severity = best_vision.get("severity", "unknown")
        valid_image = bool(best_vision.get("valid_image", False))

        # ---- 3. Evidence Agent ----
        evidence_met, evidence_reason = check_evidence_standard(
            claim_info, best_vision
        )

        # ---- 4. Risk Agent (with user history if available) ----
        risk_row = row.to_dict()
        if history is not None and user_id in history.index:
            for col, val in history.loc[user_id].to_dict().items():
                risk_row.setdefault(col, val)
        risk_flags = analyze_user_risk(risk_row)

        # ---- 5. Decision Agent ----
        decision = decide(claim_info, best_vision, claim_object)
        status = decision["claim_status"]

        matched, _ = semantic_match(claim_issue, vision_issue)
        confidence = compute_confidence(claim_issue, vision_issue, matched)
        fraud_score = compute_fraud_score(status, confidence, risk_flags)

        if not supporting_ids and status == "supported" and image_rel_paths:
            supporting_ids = [image_id_of(image_rel_paths[0])]

        supporting_str = ";".join(supporting_ids) if supporting_ids else "none"

        # Output issue_type = the visible (vision) issue when known, else claim.
        out_issue = vision_issue if vision_issue not in (None, "unknown") else claim_issue

        explanation = generate_explanation(
            claim_issue, vision_issue, status, confidence, supporting_ids
        )

        # ---- Spec row (submission) ----
        spec_rows.append({
            "user_id": user_id,
            "image_paths": row["image_paths"],
            "user_claim": claim_text,
            "claim_object": claim_object,
            "evidence_standard_met": str(bool(evidence_met)).lower(),
            "evidence_standard_met_reason": evidence_reason,
            "risk_flags": ";".join(risk_flags),
            "issue_type": out_issue,
            "object_part": object_part,
            "claim_status": status,
            "claim_status_justification": explanation,
            "supporting_image_ids": supporting_str,
            "valid_image": str(valid_image).lower(),
            "severity": severity,
        })

        # ---- Enriched row (dashboard) ----
        ui_rows.append({
            "user_id": user_id,
            "image_paths": row["image_paths"],
            "user_claim": claim_text,
            "claim_object": claim_object,
            "issue_type": out_issue,
            "object_part": object_part,
            "valid_image": valid_image,
            "severity": severity,
            "risk_flags": ";".join(risk_flags),
            "evidence_standard_met": bool(evidence_met),
            "evidence_standard_met_reason": evidence_reason,
            "claim_status": status,
            "claim_status_justification": decision["reason"],
            "supporting_image_ids": supporting_str,
            "confidence_score": round(confidence, 2),
            "fraud_score": fraud_score,
            "ai_explanation": explanation,
        })

        print(f"{user_id}: claim={claim_issue} vision={vision_issue} -> {status}")

    pd.DataFrame(spec_rows)[SPEC_COLUMNS].to_csv(SPEC_OUTPUT_PATH, index=False)
    pd.DataFrame(ui_rows).to_csv(UI_OUTPUT_PATH, index=False)

    print(f"\nWrote {SPEC_OUTPUT_PATH} (submission) and {UI_OUTPUT_PATH} (dashboard).")


if __name__ == "__main__":
    run_pipeline()
