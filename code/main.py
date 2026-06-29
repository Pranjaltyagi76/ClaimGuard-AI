import pandas as pd
import os

from agents.claim_agent import extract_claim
from agents.vision_agent import analyze_image
from agents.decision_agent import make_decision


def get_image_list(image_paths):

    paths = []

    for p in image_paths.split(";"):

        full_path = os.path.join(
            "..",
            "dataset",
            p.strip()
        )

        paths.append(full_path)

    return paths


def main():

    df = pd.read_csv("../dataset/sample_claims.csv")

    print("=" * 80)
    print("RUNNING EVALUATION")
    print("=" * 80)

    correct = 0
    total = 0

    # Only first 3 rows while debugging
    for idx, row in df.head(3).iterrows():

        print("\n" + "=" * 80)

        user_claim = row["user_claim"]

        image_paths = get_image_list(
            row["image_paths"]
        )

        claim_info = extract_claim(
            user_claim
        )

        print("CLAIM INFO:")
        print(claim_info)

        best_vision_result = None

        for image_path in image_paths:

            print("\nIMAGE:", image_path)
            print("EXISTS:", os.path.exists(image_path))

            if not os.path.exists(image_path):
                continue

            vision_result = analyze_image(
                image_path
            )

            print("VISION:")
            print(vision_result)

            if best_vision_result is None:
                best_vision_result = vision_result

            elif vision_result.get(
                "damage_visible", False
            ):
                best_vision_result = vision_result

        if best_vision_result is None:

            predicted = "not_enough_information"

        else:

            predicted = make_decision(
                claim_info,
                best_vision_result
            )

        expected = row["claim_status"]

        print("\nEXPECTED:", expected)
        print("PREDICTED:", predicted)

        if predicted == expected:
            correct += 1

        total += 1

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print("Correct:", correct)
    print("Total:", total)

    if total:
        print(
            "Accuracy:",
            round(correct / total * 100, 2),
            "%"
        )


if __name__ == "__main__":
    main()