DAMAGE_SEMANTICS = {
    "dent": ["dent", "broken_part", "deformation"],
    "crack": ["crack", "glass_shatter", "fracture"],
    "scratch": ["scratch", "abrasion"],
    "broken_part": ["broken_part", "dent", "missing_part"],
    "water_damage": ["water_damage", "stain"],
    "packaging": ["crushed_packaging", "torn_packaging"]
}


def semantic_match(claim, vision):

    for family, variants in DAMAGE_SEMANTICS.items():
        if claim in variants and vision in variants:
            return True, family

    return False, None