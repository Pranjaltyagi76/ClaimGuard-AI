import streamlit as st
import pandas as pd
import os
from PIL import Image

# -----------------------------------
# PAGE CONFIG
# -----------------------------------

st.set_page_config(
    page_title="ClaimGuard AI",
    page_icon="🛡️",
    layout="wide"
)

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
# DEMO MODE
# -----------------------------------

st.markdown("## 🎬 Demo Mode")

if st.button("▶️ Run Guided Judge Demo"):

    st.info("Running automated judge walkthrough...")

    st.markdown("### Step 1: Claim Understanding")
    st.write("AI extracts structured damage information from the claim.")

    st.markdown("### Step 2: Vision Analysis")
    st.write("Vision Agent analyzes uploaded evidence images.")

    st.markdown("### Step 3: Semantic Matching")
    st.write("Damage categories are matched semantically.")

    st.markdown("### Step 4: Evidence Evaluation")
    st.write("Evidence Agent validates visual support.")

    st.markdown("### Step 5: Risk Assessment")
    st.write("Risk Agent estimates fraud indicators.")

    st.markdown("### Step 6: Final Decision")
    st.success("Supported / Contradicted verdict generated.")

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