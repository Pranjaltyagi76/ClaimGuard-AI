import pandas as pd
import os
from agents.claim_agent import extract_claim
from agents.vision_agent import analyze_image
from agents.evidence_agent import check_evidence_standard
from agents.risk_agent import analyze_user_risk
from agents.decision_agent import decide

DATA_PATH = "../dataset/claims.csv"
IMAGE_BASE = "../dataset"
OUTPUT_PATH = "output.csv"


# ---------------------------
# Semantic Matching (your logic kept)
# ---------------------------
def semantic_match(claim_issue, vision_issue):
    if not claim_issue or not vision_issue:
        return False, None

    if claim_issue == vision_issue:
        return True, claim_issue

    claim_tokens = set(claim_issue.lower().split("_"))
    vision_tokens = set(vision_issue.lower().split("_"))
    common_tokens = claim_tokens.intersection(vision_tokens)

    if common_tokens:
        return True, "_".join(sorted(common_tokens))

    return False, None


# ---------------------------
# Fraud Score Engine (UPGRADE 1)
# ---------------------------
def compute_fraud_score(claim_status, severity, confidence):

    score = 0

    # decision impact
    if claim_status == "contradicted":
        score += 70
    elif claim_status == "supported":
        score += 20
    else:
        score += 50

    # uncertainty impact
    score += (1 - confidence) * 30

    # severity impact
    if severity == "medium":
        score += 10

    return min(100, max(0, score))


# ---------------------------
# Explanation Engine (UPGRADE 2)
# ---------------------------
def generate_explanation(claim_info, vision_info, decision, confidence):

    claim_issue = claim_info.get("issue_type")
    vision_issue = vision_info.get("issue_type")

    if decision["claim_status"] == "supported":
        return (
            f"The claim is SUPPORTED because visual evidence shows '{vision_issue}' "
            f"which aligns with the claimed damage '{claim_issue}'. "
            f"Confidence level is {round(confidence * 100)}%, indicating strong agreement."
        )

    elif decision["claim_status"] == "contradicted":
        return (
            f"The claim is CONTRADICTED because the image shows '{vision_issue}' "
            f"which does not match the claimed damage '{claim_issue}'. "
            f"Low semantic similarity detected between claim and evidence."
        )

    else:
        return (
            f"The system is UNCERTAIN due to unclear or weak visual evidence. "
            f"Manual review recommended."
        )


# ---------------------------
# Image helper
# ---------------------------
def get_first_image(image_paths):
    return os.path.join(IMAGE_BASE, image_paths.split(";")[0].strip())


# ---------------------------
# Main Pipeline
# ---------------------------
def run_pipeline():

    df = pd.read_csv(DATA_PATH)
    results = []

    for _, row in df.iterrows():

        user_id = row["user_id"]
        claim_text = row["user_claim"]
        claim_object = row["claim_object"]

        # 1. Claim Agent
        claim_info = extract_claim(claim_text)

        # 2. Vision Agent
        image_path = get_first_image(row["image_paths"])
        vision_info = analyze_image(image_path)
        print("=" * 60)
        print("USER:", user_id)
        print("CLAIM ISSUE:", claim_info.get("issue_type"))
        print("VISION ISSUE:", vision_info.get("issue_type"))
        print("VISION INFO:", vision_info)

        # 3. Evidence Agent
        evidence_met, evidence_reason = check_evidence_standard(
            claim_info,
            vision_info
        )

        # 4. Risk Agent
        risk_flags = analyze_user_risk(row)

        # 5. Decision Agent
        decision = decide(
            claim_info,
            vision_info,
            claim_object
        )

        # ---------------------------
        # Semantic + Confidence
        # ---------------------------
        
        matched, family = semantic_match(
          claim_info.get("issue_type"),
          vision_info.get("issue_type")
        )

        if claim_info.get("issue_type") == vision_info.get("issue_type"):
         confidence = 0.95

        elif matched:
         confidence = 0.80

        elif vision_info.get("issue_type") == "unknown":
         confidence = 0.50

        else:
         confidence = 0.25


        # ---------------------------
        # NEW: Fraud Score
        # ---------------------------
        fraud_score = compute_fraud_score(
          decision["claim_status"],
          vision_info.get("severity", "medium"),
          confidence
        )

        if "manual_review_required" in risk_flags:
         fraud_score = min(100, fraud_score + 10)

        # ---------------------------
        # NEW: Explanation
        # ---------------------------
        explanation = generate_explanation(
            claim_info,
            vision_info,
            decision,
            confidence
        )

        # ---------------------------
        # Store result
        # ---------------------------
        results.append({
         "user_id": user_id,
         "image_paths": row["image_paths"],
         "user_claim": claim_text,
         "claim_object": claim_object,

         "issue_type": claim_info.get("issue_type"),
         "object_part": claim_info.get("object_part"),

         "valid_image": vision_info.get("valid_image"),
         "severity": vision_info.get("severity"),

         "risk_flags": str(risk_flags),

         "evidence_standard_met": evidence_met,
         "evidence_standard_met_reason": evidence_reason,

         "claim_status": decision["claim_status"],
         "claim_status_justification": decision["reason"],

         "confidence_score": round(confidence, 2),
         "fraud_score": round(fraud_score, 2),

         "ai_explanation": explanation
        })

    out_df = pd.DataFrame(results)
    out_df.to_csv(OUTPUT_PATH, index=False)

    print("✅ output.csv generated successfully!")


if __name__ == "__main__":
    run_pipeline()