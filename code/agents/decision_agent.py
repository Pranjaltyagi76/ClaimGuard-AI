from agents.semantic_matcher import semantic_match


def decide(claim_info, vision_info, claim_object):

    claim_issue = claim_info.get("issue_type", "unknown")
    vision_issue = vision_info.get("issue_type", "unknown")

    # No usable image -> cannot decide from evidence.
    if not vision_info.get("valid_image", False):
        return {
            "claim_status": "not_enough_information",
            "reason": "image evidence is missing or unreadable",
        }

    # Image is valid but the model could not identify a damage type.
    if vision_issue in (None, "unknown") or not vision_info.get("damage_visible", False):
        return {
            "claim_status": "not_enough_information",
            "reason": f"no clear visible damage to confirm claim '{claim_issue}'",
        }

    if claim_issue == vision_issue:
        return {
            "claim_status": "supported",
            "reason": f"exact match: claim and image both show '{claim_issue}'",
        }

    matched, family = semantic_match(claim_issue, vision_issue)
    if matched:
        return {
            "claim_status": "supported",
            "reason": f"semantic match ({family}): claim '{claim_issue}' ~ image '{vision_issue}'",
        }

    return {
        "claim_status": "contradicted",
        "reason": f"mismatch: claim '{claim_issue}' vs image '{vision_issue}'",
    }
