import streamlit as st
import pandas as pd
import os
import sys
import tempfile
from PIL import Image
try:
    import pillow_avif  # noqa: F401 - dataset images are AVIF (with .jpg names)
except ImportError:
    pass

# Make the local agents importable regardless of launch directory.
# (Not a Streamlit command, so it is safe before set_page_config.)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

# -----------------------------------
# PAGE CONFIG
# -----------------------------------

st.set_page_config(
    page_title="ClaimGuard AI",
    page_icon="🛡️",
    layout="wide"
)

# Interactive tab must be snappy: no proactive throttle and no long retry
# backoff (a rate-limited call should fail fast to manual review, not hang).
# Set BEFORE the agents import (they read these at import time).
os.environ.setdefault("GEMINI_THROTTLE", "0")
os.environ.setdefault("GEMINI_MAX_RETRIES", "1")

# Bridge Streamlit Cloud secrets -> env vars for the agents. Must come AFTER
# set_page_config (st.secrets access counts as a Streamlit command). The agents
# import lazily on button-click, so the key is set before vision_agent loads.
try:
    for _k in ("GEMINI_API_KEY", "GEMINI_MODEL"):
        if _k in st.secrets:
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass

# -----------------------------------
# CUSTOM CSS
# -----------------------------------

st.markdown("""
<style>

/* ===========================
   GLOBAL
=========================== */

html, body, [class*="css"]{
    font-family:Inter,sans-serif;
}

.main{
    background:#0f1117;
}

.block-container{
    padding-top:2rem;
    padding-left:3rem;
    padding-right:3rem;
    max-width:1500px;
}


/* ===========================
   HEADINGS
=========================== */

h1{
    font-size:2.8rem;
    font-weight:800;
    color:white;
}

h2{
    font-size:1.8rem;
    font-weight:700;
    color:#f5f5f5;
}

h3{
    font-weight:600;
}


/* ===========================
   METRIC CARDS
=========================== */

div[data-testid="metric-container"]{

    background:#181b22;

    border:1px solid #2f3441;

    border-radius:18px;

    padding:24px;

    box-shadow:
        0px 8px 25px rgba(0,0,0,.25);

    transition:.3s;
}

div[data-testid="metric-container"]:hover{

    transform:translateY(-4px);

    border:1px solid #4da3ff;
}


/* ===========================
   BUTTON
=========================== */

.stButton>button{

    width:100%;

    height:54px;

    border-radius:14px;

    border:none;

    background:#2563eb;

    color:white;

    font-size:18px;

    font-weight:700;

    transition:.25s;
}

.stButton>button:hover{

    background:#1d4ed8;

    transform:scale(1.02);
}


/* ===========================
   DATAFRAME
=========================== */

div[data-testid="stDataFrame"]{

    border-radius:18px;

    overflow:hidden;

    border:1px solid #30343f;

}


/* ===========================
   PROGRESS BAR
=========================== */

div[data-testid="stProgress"]>div{

    border-radius:20px;
}

div[data-testid="stProgress"]>div>div{

    border-radius:20px;
}


/* ===========================
   FILE UPLOADER
=========================== */

[data-testid="stFileUploader"]{

    border:2px dashed #3b82f6;

    border-radius:18px;

    padding:22px;

    background:#17191f;

}


/* ===========================
   TEXT AREA
=========================== */

textarea{

    border-radius:15px !important;

    font-size:16px !important;

}


/* ===========================
   IMAGES
=========================== */

img{

    border-radius:20px;

    box-shadow:
        0px 10px 30px rgba(0,0,0,.35);

}


/* ===========================
   SIDEBAR
=========================== */

section[data-testid="stSidebar"]{

    background:#17191f;

}


/* ===========================
   SCROLLBAR
=========================== */

::-webkit-scrollbar{

    width:8px;
}

::-webkit-scrollbar-thumb{

    background:#3d4a63;

    border-radius:20px;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------------
# PATHS
# -----------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "output.csv"
)

DATASET_DIR = os.path.join(
    os.path.dirname(BASE_DIR),
    "dataset"
)

# -----------------------------------
# HEADER
# -----------------------------------

st.title("🛡️ ClaimGuard AI")
st.caption("Multi-Agent Insurance Claim Verification System")

st.markdown("""
### AI-Powered Multi-Agent Insurance Claim Verification

Verify insurance claims using collaborative AI agents for
claim understanding, visual inspection, evidence validation,
fraud risk assessment, and final decision making.

**Pipeline**

📄 Claim Extraction
        ↓
👁️ Visual Damage Analysis
        ↓
📑 Evidence Verification
        ↓
🚨 Fraud Risk Assessment
        ↓
✅ Final AI Decision
""")

# -----------------------------------
# TRY IT LIVE (real multi-agent pipeline)
# -----------------------------------

st.markdown("## 🧪 Try It Live")
st.caption(
    "Upload a damage photo (or pick a sample), describe the claim, and watch "
    "all five agents run in real time."
)


def _run_live_pipeline(image_path, claim_text, claim_object):
    """Run the full agent pipeline on one image + claim and render the steps."""
    from agents.claim_agent import extract_claim
    from agents.vision_agent import analyze_image
    from agents.evidence_agent import check_evidence_standard
    from agents.risk_agent import analyze_user_risk
    from agents.decision_agent import decide

    steps = st.container()

    with steps:
        # 1) Claim Agent
        st.markdown("#### 📄 Claim Agent")
        claim_info = extract_claim(claim_text)
        st.json(claim_info)

        # 2) Vision Agent
        st.markdown("#### 👁️ Vision Agent (Gemini)")
        with st.spinner("Analyzing the image with Gemini..."):
            vision_info = analyze_image(image_path)
        if not vision_info.get("valid_image") and vision_info.get("issue_type") == "unknown":
            st.warning(
                "Vision could not analyze the image (missing API key, rate "
                "limit, or unreadable image). The claim will route to manual "
                "review — the system does not guess."
            )
        st.json(vision_info)

        # 3) Evidence Agent
        st.markdown("#### 📑 Evidence Agent")
        evidence_met, evidence_reason = check_evidence_standard(claim_info, vision_info)
        st.write(f"**Evidence standard met:** `{evidence_met}` — {evidence_reason}")

        # 4) Risk Agent
        st.markdown("#### 🚨 Risk Agent")
        risk_flags = analyze_user_risk({"user_claim": claim_text})
        st.write("**Risk flags:** " + ", ".join(f"`{f}`" for f in risk_flags))
        if "text_instruction_present" in risk_flags:
            st.error("⚠️ Prompt-injection detected in the claim text — flagged, not obeyed.")

        # 5) Decision Agent
        st.markdown("#### ✅ Decision Agent")
        decision = decide(claim_info, vision_info, claim_object)
        status = decision["claim_status"]

        if status == "supported":
            st.success(f"**SUPPORTED** ✅ — {decision['reason']}")
        elif status == "contradicted":
            st.error(f"**CONTRADICTED** ❌ — {decision['reason']}")
        else:
            st.warning(f"**NOT ENOUGH INFORMATION** ⚠️ — {decision['reason']}")


_have_key = bool(os.getenv("GEMINI_API_KEY"))
if not _have_key:
    st.info(
        "ℹ️ Live vision needs a Gemini API key. Add `GEMINI_API_KEY` in the app's "
        "**Settings → Secrets** to enable real-time analysis. The pipeline still "
        "runs and will honestly route to manual review without it."
    )

# Friendly labels -> (image path, prefilled claim, object) for instant demos.
# These map to already-analyzed images, so results are real and instant.
SAMPLE_CASES = {
    "🚗 Car — windshield (crack)": (
        "images/test/case_004/img_1.jpg",
        "A stone hit my windshield and it looks shattered.", "car"),
    "🚗 Car — bumper (scratch)": (
        "images/test/case_001/img_2.jpg",
        "The front bumper of my car got scratched in a parking incident.", "car"),
    "🚗 Car — door (dent)": (
        "images/test/case_003/img_1.jpg",
        "There is a deep dent on my car door.", "car"),
}

with st.form("live_form"):
    st.markdown("**Fastest way to see it work:** pick a sample below (instant, "
                "real results). Uploading your own photo needs live API quota.")

    sample_choice = st.selectbox(
        "▶️ Sample case (recommended)", ["(choose your own below)"] + list(SAMPLE_CASES),
    )

    col_a, col_b = st.columns([1, 1])
    with col_a:
        claim_object_live = st.selectbox("Object type", ["car", "laptop", "package"])
        claim_text_live = st.text_area(
            "Claim description",
            value="The front bumper of my car is damaged after a parking incident.",
            height=110,
        )
    with col_b:
        uploaded = st.file_uploader(
            "…or upload your own damage image",
            type=["jpg", "jpeg", "png", "avif", "webp"],
        )

    submitted = st.form_submit_button("▶️ Run the multi-agent pipeline")

if submitted:
    live_image_path = None

    if sample_choice in SAMPLE_CASES:
        rel, claim_text_live, claim_object_live = SAMPLE_CASES[sample_choice]
        live_image_path = os.path.join(DATASET_DIR, rel)
    elif uploaded is not None:
        suffix = os.path.splitext(uploaded.name)[1] or ".jpg"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(uploaded.getbuffer())
        tmp.flush()
        live_image_path = tmp.name

    if live_image_path is None:
        st.warning("Please upload an image or pick a sample first.")
    else:
        try:
            st.image(Image.open(live_image_path), caption="Evidence under review", width=360)
        except Exception:
            st.caption("(preview unavailable)")
        _run_live_pipeline(live_image_path, claim_text_live, claim_object_live)

# -----------------------------------
# LOAD DATA
# -----------------------------------

if not os.path.exists(OUTPUT_PATH):

    st.error("❌ output.csv not found")
    st.stop()

df = pd.read_csv(OUTPUT_PATH)

# -----------------------------------
# METRICS
# -----------------------------------

st.divider()

supported = (df["claim_status"] == "supported").sum()
contradicted = (df["claim_status"] == "contradicted").sum()
uncertain = (df["claim_status"] == "not_enough_information").sum()

col1, col2, col3, col4 = st.columns(4)

col1.metric("📂 Claims Processed", len(df))
col2.metric("✅ Verified", supported)
col3.metric("❌ Rejected", contradicted)
col4.metric("⚠ Uncertain", uncertain)

# -----------------------------------
# ANALYTICS
# -----------------------------------

st.divider()

st.subheader("📊 Performance Dashboard")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Average Confidence",
    f"{round(df['confidence_score'].mean() * 100)}%"
)

c2.metric(
    "Average Fraud Risk",
    f"{round(df['fraud_score'].mean())}/100"
)

c3.metric(
    "Evidence Pass Rate",
    f"{round(df['evidence_standard_met'].mean() * 100)}%"
)

st.divider()

left, right = st.columns(2)

with left:

    st.subheader("📊 Verdict Distribution")

    st.bar_chart(
        df["claim_status"].value_counts()
    )

with right:

    st.subheader("🚨 Severity Distribution")

    st.bar_chart(
        df["severity"].value_counts()
    )

# -----------------------------------
# TABLE
# -----------------------------------

st.divider()

st.subheader("📋 Processed Claims")

_total_images = int(
    df["image_paths"].astype(str).apply(lambda s: len([p for p in s.split(";") if p.strip()])).sum()
)

st.markdown(
    f"""
This is the **batch output** of ClaimGuard AI. We ran the full multi-agent
pipeline on **all {len(df)} claims** ({_total_images} evidence images) from the
test set and summarized every result here for review.

Each row is **one claim**, processed automatically through all five agents —
📄 claim understanding → 👁️ Gemini vision analysis → 📑 evidence check →
🚨 fraud/risk scoring → ✅ final decision. Verdict mix: **{supported} supported**,
**{contradicted} contradicted**, **{uncertain} routed to manual review**.

> 💡 The table below is the summary. To inspect any single claim in detail —
> its images, agent reasoning, and confidence — use the
> **🔎 Claim Investigation Panel** further down.
"""
)

st.dataframe(
    df,
    use_container_width=True
)

csv = df.to_csv(index=False)

st.download_button(
    "📥 Download Results CSV",
    csv,
    file_name="output.csv",
    mime="text/csv"
)

# -----------------------------------
# CLAIM INSPECTOR
# -----------------------------------

st.divider()

st.subheader("🔎 Claim Investigation Panel")

st.markdown(
    """
Want to **deep-dive the results one by one?** This is the place. Pick any user
below to open that single claim and review everything ClaimGuard AI decided for
it — the original customer conversation, the AI's verdict and reasoning,
severity, confidence and fraud-risk scores, the flagged risks, and the actual
evidence images side by side.

Use it to **audit the system's judgment** on any individual case.
"""
)

selected_user = st.selectbox(
    "Select User ID",
    df["user_id"].unique()
)

row = df[df["user_id"] == selected_user].iloc[0]

left_panel, right_panel = st.columns(2)

# -----------------------------------
# CLAIM DETAILS
# -----------------------------------

with left_panel:

    st.markdown("### 🧾 Claim Details")

    st.write("**Claim:**")
    st.write(row["user_claim"])

    st.write("**Object:**", row["claim_object"])
    st.write("**Issue Type:**", row["issue_type"])
    st.write("**Object Part:**", row["object_part"])

    status = row["claim_status"]

    if status == "supported":
        st.success("SUPPORTED CLAIM ✅")

    elif status == "contradicted":
        st.error("CONTRADICTED CLAIM ❌")

    else:
        st.warning("NOT ENOUGH INFORMATION ⚠️")

    st.markdown("### 📌 Decision Reason")

    st.info(
        row["claim_status_justification"]
    )

# -----------------------------------
# AI ANALYSIS
# -----------------------------------

with right_panel:

    st.markdown("### 🤖 AI Analysis")

    severity = row["severity"]

    st.write("**Severity:**", severity)

    if severity == "high":
        st.error("🔴 High Severity")

    elif severity == "medium":
        st.warning("🟠 Medium Severity")

    elif severity == "low":
        st.success("🟢 Low Severity")

    confidence = float(
        row.get(
            "confidence_score",
            0.5
        )
    )

    st.markdown("### 🧠 Confidence Score")

    st.progress(confidence)

    st.metric(
        "Confidence",
        f"{int(confidence * 100)}%"
    )

    fraud_score = int(
        row.get(
            "fraud_score",
            50
        )
    )

    st.markdown("### 🚨 Fraud Risk")

    st.progress(
        fraud_score / 100
    )

    st.metric(
        "Fraud Score",
        f"{fraud_score}/100"
    )

    st.markdown("### ⚠️ Risk Flags")

    st.code(
        str(row["risk_flags"])
    )

    st.markdown("### 📑 Evidence Status")

    st.write(
        row["evidence_standard_met"]
    )

    st.code(
        row["evidence_standard_met_reason"]
    )

    if "ai_explanation" in row:

        st.markdown(
            "### 🧠 AI Explanation"
        )

        st.info(
            row["ai_explanation"]
        )

# -----------------------------------
# IMAGES
# -----------------------------------

st.divider()

st.subheader("🖼️ Evidence Images")

_supporting = str(row.get("supporting_image_ids", "none"))

st.markdown(
    f"""
These are the **actual evidence photos submitted with this claim** — the
reference/test images our 👁️ Vision Agent inspected with Gemini. The system
looks at **every image** (not just the first) and picks the one(s) that truly
show the claimed damage, which is what it cites as proof for its verdict.

**Image(s) supporting this decision:** `{_supporting}`
"""
)

image_paths = str(
    row["image_paths"]
).split(";")

cols = st.columns(
    len(image_paths)
)

for idx, img_path in enumerate(
    image_paths
):

    clean_path = (
        img_path
        .strip()
        .replace("\\", "/")
    )

    full_path = os.path.join(
        DATASET_DIR,
        clean_path
    )

    with cols[idx]:

        if os.path.exists(
            full_path
        ):

            image = Image.open(
                full_path
            )

            st.image(
                image,
                caption=f"Evidence {idx+1}",
                use_container_width=True
            )

        else:

            st.warning(
                f"Image {idx+1} not found"
            )

# -----------------------------------
# DEBUG
# -----------------------------------

with st.expander(
    "🧠 Raw AI Output"
):

    st.json(
        row.to_dict()
    )


st.divider()

st.caption(
    "ClaimGuard AI • Multi-Agent Insurance Claim Verification • Built with Streamlit, Gemini 2.5 Flash and Python"
)