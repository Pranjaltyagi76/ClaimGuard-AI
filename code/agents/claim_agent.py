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

# Object parts written in their canonical (underscore) output form,
# mapped from the natural-language variants a customer might type.
# Order matters: more specific / multi-word phrases are checked first.
PART_ALIASES = [
    # car
    ("front bumper", "front_bumper"),
    ("rear bumper", "rear_bumper"),
    ("side mirror", "side_mirror"),
    ("quarter panel", "quarter_panel"),
    ("windshield", "windshield"),
    ("headlight", "headlight"),
    ("taillight", "taillight"),
    ("tail light", "taillight"),
    ("fender", "fender"),
    ("bumper", "front_bumper"),
    ("hood", "hood"),
    ("door", "door"),
    # laptop
    ("screen", "screen"),
    ("keyboard", "keyboard"),
    ("trackpad", "trackpad"),
    ("touchpad", "trackpad"),
    ("hinge", "hinge"),
    ("lid", "lid"),
    # package
    ("package corner", "package_corner"),
    ("package side", "package_side"),
    ("box", "box"),
    ("seal", "seal"),
    ("label", "label"),
    ("contents", "contents"),
    ("item", "item"),
    # shared / generic (kept last so specific parts win)
    ("corner", "corner"),
    ("body", "body"),
    ("port", "port"),
    ("base", "base"),
]


def _extract_customer_text(user_claim):
    """The claim belongs to the CUSTOMER, not the agent/support rep.

    The transcript interleaves 'Customer:' / 'Agent:' / 'Support:' turns.
    Parsing the whole blob lets a part the agent *asks about* leak into the
    result (e.g. 'Is this about the door?' -> object_part=door). We keep only
    the customer's own words when speaker labels are present.
    """
    turns = re.split(r"\|", str(user_claim))
    customer_lines = []

    for turn in turns:
        label, _, said = turn.partition(":")
        if said and re.search(r"customer|cliente|client", label, re.I):
            customer_lines.append(said)

    if customer_lines:
        return " ".join(customer_lines).lower()

    # No recognizable speaker labels -> fall back to the full text.
    return str(user_claim).lower()


def _find_whole_word(text, phrase):
    """Match `phrase` on word boundaries so 'port' does not match 'Support'."""
    pattern = r"\b" + re.escape(phrase) + r"\b"
    return re.search(pattern, text) is not None


def extract_claim(user_claim):

    text = _extract_customer_text(user_claim)

    # ------------------
    # ISSUE TYPE (whole-word, customer text only)
    # ------------------

    if _find_whole_word(text, "shatter") or _find_whole_word(text, "shattered"):
        issue = "glass_shatter"

    elif _find_whole_word(text, "dent") or _find_whole_word(text, "dented") \
            or _find_whole_word(text, "dents"):
        issue = "dent"

    elif _find_whole_word(text, "scratch") or _find_whole_word(text, "scrape") \
            or _find_whole_word(text, "scratched"):
        issue = "scratch"

    elif _find_whole_word(text, "crack") or _find_whole_word(text, "cracked"):
        issue = "crack"

    elif _find_whole_word(text, "missing") or _find_whole_word(text, "faltan") \
            or _find_whole_word(text, "came off"):
        issue = "missing_part"

    elif _find_whole_word(text, "torn"):
        issue = "torn_packaging"

    elif _find_whole_word(text, "crushed") or _find_whole_word(text, "crush") \
            or _find_whole_word(text, "dab"):
        issue = "crushed_packaging"

    elif _find_whole_word(text, "water") or _find_whole_word(text, "wet") \
            or _find_whole_word(text, "liquid"):
        issue = "water_damage"

    elif _find_whole_word(text, "stain") or _find_whole_word(text, "oil") \
            or _find_whole_word(text, "mark"):
        issue = "stain"

    elif _find_whole_word(text, "broken") or _find_whole_word(text, "broke") \
            or _find_whole_word(text, "damaged") or _find_whole_word(text, "toot"):
        issue = "broken_part"

    else:
        issue = "unknown"

    # ------------------
    # OBJECT PART (whole-word, first specific match wins)
    # ------------------

    object_part = "unknown"

    for phrase, canonical in PART_ALIASES:
        if _find_whole_word(text, phrase):
            object_part = canonical
            break

    return {
        "issue_type": issue,
        "object_part": object_part
    }
