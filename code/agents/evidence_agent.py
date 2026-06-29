def check_evidence_standard(
    claim_info,
    vision_info
):

    issue_type = vision_info.get("issue_type", "unknown")

    if issue_type == "unknown":
        return (
            False,
            "vision model uncertain"
        )

    if vision_info.get("damage_visible", False):
        return (
            True,
            "damage visible"
        )

    return (
        False,
        "damage not visible"
    )