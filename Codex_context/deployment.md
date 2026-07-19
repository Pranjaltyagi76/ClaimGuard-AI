# Deployment

## Strategy

**Offline inference, static serving.** The expensive vision pass runs once via
`generate_output.py` and writes `code/output.csv`. The public app (`ui_app.py`)
only *reads* that file plus the committed images — so the live URL needs **no API
key at runtime**, can't fail on quota, and is essentially free to host.

Target platform: **Streamlit Community Cloud** (free, GitHub-native).

## Prerequisites

- Public GitHub repo: `Pranjaltyagi76/ClaimGuard-AI`
- `requirements.txt` pinned to install-safe versions
- `code/output.csv` (precomputed results) + `dataset/images/` committed
- `.streamlit/config.toml` for the dark theme

## Deploy steps (Streamlit Community Cloud)

1. Go to **https://share.streamlit.io** and sign in with GitHub.
2. **New app** →
   - Repository: `Pranjaltyagi76/ClaimGuard-AI`
   - Branch: `main`
   - **Main file path: `code/ui_app.py`**
3. (Optional) **Advanced settings → Secrets**:
   ```toml
   GEMINI_API_KEY = "your_key_here"
   ```
   Only needed if you later add live analysis; the dashboard runs without it.
4. **Deploy.** You get a URL like `https://claimguard-ai.streamlit.app`.
5. Paste the URL into the README "Live demo" slot, commit, and push — Streamlit
   auto-redeploys on every push to `main`.

## Regenerating real results (with a Gemini key)

```bash
# .env at repo root
GEMINI_API_KEY=your_key_here
# optional model override:
# GEMINI_MODEL=gemini-2.0-flash

cd code
python generate_output.py     # writes ../output.csv (spec) + code/output.csv (dashboard)
```

Then commit both CSVs and push → the live app updates.

> **Note:** local Python 3.14 has no wheels yet for pandas/numpy. Use Python
> **3.12** (`py -3.12 -m venv venv`) or **Google Colab** to run the regeneration.

## Environment variables

| Variable | Purpose | Where |
| --- | --- | --- |
| `GEMINI_API_KEY` | Gemini access for vision | `.env` / Streamlit Secrets |
| `GEMINI_MODEL` | Override vision model (default `gemini-2.5-flash`) | `.env` (optional) |
| `GEMINI_THROTTLE` | Seconds between vision calls (default `5`, for free-tier RPM) | `.env` (optional) |

## Rollback

Streamlit deploys track the Git commit. To roll back, revert the commit (or
redeploy an earlier one) from the Streamlit app dashboard.

## Post-deploy checklist

- [ ] Live URL loads and renders metrics
- [ ] Claim Investigation Panel works; evidence images display
- [ ] README "Live demo" link updated
- [ ] `output.csv`, `evaluation/`, and `chat_transcript` ready for submission
