import os
import json
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

# ----------------------------------
# CONFIG
# ----------------------------------

USE_MOCK = False

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-flash")


# ----------------------------------
# CACHE HELPERS
# ----------------------------------

def get_cache_path(image_path):
    image_id = image_path.replace("\\", "_")
    image_id = image_id.replace("/", "_")
    image_id = image_id.replace(":", "_")

    return os.path.join(
        CACHE_DIR,
        image_id + ".json"
    )


# ----------------------------------
# MAIN VISION AGENT
# ----------------------------------

def analyze_image(image_path):

    cache_path = get_cache_path(image_path)

    # ------------------------------
    # Use Cached Result
    # ------------------------------
    if os.path.exists(cache_path):

        try:
            with open(cache_path, "r") as f:
                return json.load(f)

        except Exception:
            pass

    # ------------------------------
    # Mock Mode
    # ------------------------------
    if USE_MOCK:

        result = {
            "valid_image": True,
            "issue_type": "broken_part",
            "object_part": "visible_damage",
            "severity": "medium",
            "damage_visible": True,
            "risk_flags": []
        }

        with open(cache_path, "w") as f:
            json.dump(result, f, indent=2)

        return result

    # ------------------------------
    # Check Image Exists
    # ------------------------------
    if not os.path.exists(image_path):

        result = {
            "valid_image": False,
            "issue_type": "unknown",
            "object_part": "unknown",
            "severity": "unknown",
            "damage_visible": False,
            "risk_flags": ["image_not_found"]
        }

        return result

    # ------------------------------
    # Load Image
    # ------------------------------
    try:
        image = Image.open(image_path)

    except Exception as e:

        print("IMAGE LOAD ERROR:", e)

        return {
            "valid_image": False,
            "issue_type": "unknown",
            "object_part": "unknown",
            "severity": "unknown",
            "damage_visible": False,
            "risk_flags": ["image_read_error"]
        }

    # ------------------------------
    # Gemini Prompt
    # ------------------------------
    prompt = """
You are a professional insurance damage assessor.

Analyze the image carefully.

Return ONLY valid JSON.

{
  "valid_image": true,
  "issue_type": "",
  "object_part": "",
  "severity": "",
  "damage_visible": true,
  "risk_flags": []
}

Allowed issue_type:

dent
scratch
crack
glass_shatter
broken_part
missing_part
torn_packaging
crushed_packaging
water_damage
stain
none
unknown

Allowed severity:

none
low
medium
high
unknown

Rules:

- Detect only visible damage.
- Do not guess hidden damage.
- Return JSON only.
- If unsure, use "unknown".
"""

    # ------------------------------
    # Gemini Analysis
    # ------------------------------
    try:

        print(f"Analyzing image: {image_path}")

        response = model.generate_content(
            [prompt, image]
        )

        clean_text = (
            response.text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        result = json.loads(clean_text)

    except Exception as e:

        print("VISION ERROR:", e)

        # Graceful fallback
        result = {
            "valid_image": True,
            "issue_type": "broken_part",
            "object_part": "visible_damage",
            "severity": "medium",
            "damage_visible": True,
            "risk_flags": ["manual_review_required"]
        }

    # ------------------------------
    # Save Cache
    # ------------------------------
    try:

        with open(cache_path, "w") as f:
            json.dump(
                result,
                f,
                indent=2
            )

    except Exception:
        pass

    return result