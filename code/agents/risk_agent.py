def analyze_user_risk(user_row):

    risk_flags = []

    claim_text = str(user_row.get("user_claim", "")).lower()

    # basic keyword-based risk inference (dataset-safe)
    if any(word in claim_text for word in ["urgent", "broken", "crushed", "severe"]):
        risk_flags.append("high_severity_language")

    if any(word in claim_text for word in ["maybe", "not sure", "think", "possible"]):
        risk_flags.append("uncertain_claim")

    # default safe behavior
    if len(risk_flags) == 0:
        return ["low_risk"]

    return risk_flags