import os
import json
import time
from PIL import Image
try:
    import pillow_avif  # noqa: F401 - registers AVIF support with Pillow
except ImportError:
    pass
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

# Model is configurable via env so we can swap without editing code.
# gemini-2.5-flash is vision-capable and available on current free-tier keys.
# Override with GEMINI_MODEL (e.g. gemini-flash-latest) if you prefer.
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Rate-limit handling for the batch run.
MAX_RETRIES = 5
RETRY_BASE_DELAY = 8  # seconds; doubles each retry (8, 16, 32, ...)
# Proactive throttle to stay under free-tier RPM (~10/min). Configurable.
THROTTLE_DELAY = float(os.getenv("GEMINI_THROTTLE", "5"))

# Cache-only mode: never call the API; uncached images honestly report as
# not-yet-analyzed (-> not_enough_information / manual review downstream).
CACHE_ONLY = os.getenv("VISION_CACHE_ONLY", "0") == "1"

model = genai.GenerativeModel(MODEL_NAME)


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
    # Cache-Only Mode (no API calls)
    # ------------------------------
    if CACHE_ONLY:
        # Not analyzed yet -> report honestly; do NOT invent a result.
        return {
            "valid_image": False,
            "issue_type": "unknown",
            "object_part": "unknown",
            "severity": "unknown",
            "damage_visible": False,
            "risk_flags": ["manual_review_required"]
        }

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

        if THROTTLE_DELAY > 0:
            time.sleep(THROTTLE_DELAY)

        # Retry with exponential backoff on rate limits (HTTP 429). Free-tier
        # keys allow only a handful of requests per minute, so a transient 429
        # should wait and retry rather than fall through to the honest fallback.
        last_err = None
        for attempt in range(MAX_RETRIES):
            try:
                response = model.generate_content(
                    [prompt, image],
                    generation_config={
                        "response_mime_type": "application/json",
                        "temperature": 0,
                    },
                )
                break
            except Exception as call_err:
                last_err = call_err
                if "429" in str(call_err) and attempt < MAX_RETRIES - 1:
                    wait = RETRY_BASE_DELAY * (2 ** attempt)
                    print(f"  rate limited, retrying in {wait}s "
                          f"(attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(wait)
                    continue
                raise
        else:
            raise last_err

        clean_text = (
            response.text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        result = json.loads(clean_text)

    except Exception as e:

        print("VISION ERROR:", e)

        # HONEST fallback: if the model call fails we must NOT invent a
        # damage type. Returning "unknown" lets the decision layer downgrade
        # the claim to not_enough_information instead of silently fabricating
        # "broken_part" for every row.
        result = {
            "valid_image": False,
            "issue_type": "unknown",
            "object_part": "unknown",
            "severity": "unknown",
            "damage_visible": False,
            "risk_flags": ["manual_review_required"]
        }

    # ------------------------------
    # Save Cache
    # ------------------------------
    # Only cache REAL analyses. Caching the error fallback would poison the
    # cache: a transient rate-limit failure would look permanent on re-runs.
    is_error_fallback = (
        not result.get("valid_image", False)
        and result.get("issue_type") == "unknown"
    )

    if not is_error_fallback:
        try:
            with open(cache_path, "w") as f:
                json.dump(result, f, indent=2)
        except Exception:
            pass

    return result