import re

ISSUE_TYPES = [
    "dent",
    "scratch",
    "crack",
    "glass_shatter",
    "broken_part",
    "missing_part",
    "torn_packaging",
    "crushed_packaging",
    "water_damage",
    "stain"
]


def extract_claim(user_claim):

    text = user_claim.lower()

    # ------------------
    # ISSUE TYPE
    # ------------------

    if any(word in text for word in ["dent", "hail dent"]):
        issue = "dent"

    elif any(word in text for word in ["scratch", "scrape", "mark"]):
        issue = "scratch"

    elif "crack" in text:
        issue = "crack"

    elif any(word in text for word in ["shatter", "shattered"]):
        issue = "glass_shatter"

    elif any(word in text for word in ["broken", "damaged", "damage"]):
        issue = "broken_part"

    elif "missing" in text:
        issue = "missing_part"

    elif "water" in text:
        issue = "water_damage"

    elif "stain" in text:
        issue = "stain"

    elif "torn" in text:
        issue = "torn_packaging"

    elif "crushed" in text:
        issue = "crushed_packaging"

    else:
        issue = "unknown"

    # ------------------
    # OBJECT PART
    # ------------------

    parts = [
        # car
        "front bumper",
        "rear bumper",
        "door",
        "hood",
        "windshield",
        "side mirror",
        "headlight",
        "taillight",
        "fender",
        "quarter panel",

        # laptop
        "screen",
        "keyboard",
        "trackpad",
        "hinge",
        "lid",
        "corner",
        "port",
        "base",

        # package
        "box",
        "seal",
        "label",
        "contents",
        "item"
    ]

    object_part = "unknown"

    for part in parts:
        if part in text:
            object_part = part
            break

    return {
        "issue_type": issue,
        "object_part": object_part
    }