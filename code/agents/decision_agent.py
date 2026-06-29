from agents.semantic_matcher import semantic_match

def decide(claim_info, vision_info, claim_object):

    claim_issue = claim_info.get("issue_type", "unknown")
    vision_issue = vision_info.get("issue_type", "unknown")

    if not vision_info.get("valid_image", False):
        return {
            "claim_status": "not_enough_information",
            "reason": "invalid image"
        }

    matched, family = semantic_match(
        claim_issue,
        vision_issue
    )

    if claim_issue == vision_issue:
        return {
            "claim_status": "supported",
            "reason": "exact match"
        }

    if matched:
        return {
            "claim_status": "supported",
            "reason": f"semantic match ({family})"
        }

    return {
        "claim_status": "contradicted",
        "reason": f"claim={claim_issue}, vision={vision_issue}"
    }