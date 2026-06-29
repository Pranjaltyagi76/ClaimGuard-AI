VALID_CAR_PARTS = {
    "front bumper": "front_bumper",
    "rear bumper": "rear_bumper",
    "door": "door",
    "hood": "hood",
    "windshield": "windshield",
    "side mirror": "side_mirror",
    "headlight": "headlight",
    "taillight": "taillight",
    "fender": "fender",
    "quarter panel": "quarter_panel",
    "body": "body"
}


def normalize_object_part(part):

    text = str(part).lower()

    for key, value in VALID_CAR_PARTS.items():
        if key in text:
            return value

    return "unknown"