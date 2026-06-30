# 🛡️ ClaimGuard AI

> **A Multi-Agent AI System for Automated Insurance Claim Verification using Vision-Language Models, Semantic Reasoning, and Explainable AI.**

ClaimGuard AI is an end-to-end insurance claim verification system that combines computer vision, natural language understanding, semantic matching, fraud assessment, and explainable AI through a collaborative multi-agent architecture.

The system analyzes both customer claims and uploaded damage images to determine whether a claim is supported by visual evidence while providing confidence scores, fraud risk estimation, and human-readable explanations.

---

# ✨ Features

* 🤖 Multi-Agent AI Architecture
* 👁️ Vision-Language Damage Analysis using Gemini
* 📄 Natural Language Claim Understanding
* 🔍 Semantic Damage Matching
* 📑 Evidence Verification
* 🚨 Fraud Risk Assessment
* 📊 Confidence Scoring
* 💡 Explainable AI Decision Making
* 🖥️ Interactive Streamlit Dashboard
* ⚡ Image Analysis Caching

---

# 🏗️ System Architecture

```text
                    Customer Claim
                          │
                          ▼
                  📄 Claim Agent
                          │
                          ▼
                 👁️ Vision Agent
                          │
                          ▼
               📑 Evidence Agent
                          │
                          ▼
                 🚨 Risk Agent
                          │
                          ▼
               ✅ Decision Agent
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
 Confidence Score                 Fraud Score
          │                               │
          └───────────────┬───────────────┘
                          ▼
               Explainable AI Verdict
```

---

# 🤖 Multi-Agent Workflow

## 📄 Claim Agent

Extracts structured information from natural language insurance claims.

**Responsibilities**

* Damage extraction
* Object part identification
* Claim normalization

Example

```json
{
    "issue_type":"dent",
    "object_part":"front bumper"
}
```

---

## 👁️ Vision Agent

Uses Gemini Vision to inspect uploaded evidence images.

Outputs

* Damage category
* Damaged component
* Severity estimation
* Image validity
* Visible damage detection

---

## 📑 Evidence Agent

Evaluates whether uploaded images sufficiently support the customer's claim.

Checks

* Visible damage
* Image quality
* Evidence consistency

---

## 🚨 Risk Agent

Identifies potential fraud indicators.

Examples

* Ambiguous language
* Suspicious wording
* Missing evidence
* Manual review requirements

---

## ✅ Decision Agent

Combines outputs from all previous agents to generate the final decision.

Possible Results

| Decision                  | Description                        |
| ------------------------- | ---------------------------------- |
| ✅ Supported               | Visual evidence supports the claim |
| ❌ Contradicted            | Evidence conflicts with the claim  |
| ⚠️ Not Enough Information | Manual review recommended          |

---

# 🧠 Semantic Reasoning

Rather than relying on exact keyword matching, ClaimGuard AI performs semantic matching between textual claims and detected visual damage.

Examples

```text
Dent
↕
Broken Part
↕

Structural Damage
```

```text
Glass Shatter
↕
Crack
```

This improves robustness when users describe damage differently from what the vision model detects.

---

# 📊 Dashboard

The interactive Streamlit dashboard provides:

* 📂 Claims Overview
* 📈 Performance Dashboard
* 🔍 Claim Investigation Panel
* 🤖 AI Assessment
* 📊 Confidence Visualization
* 🚨 Fraud Risk Meter
* 🖼️ Evidence Viewer
* 💡 Explainable AI
* 🧠 Agent Debug Output

---

# 📂 Project Structure

```text
ClaimGuard-AI/

│
├── code/
│   ├── agents/
│   │   ├── claim_agent.py
│   │   ├── vision_agent.py
│   │   ├── evidence_agent.py
│   │   ├── risk_agent.py
│   │   ├── decision_agent.py
│   │   └── semantic_matcher.py
│   │
│   ├── generate_output.py
│   ├── ui_app.py
│   ├── output.csv
│   └── cache/
│
├── dataset/
│   ├── claims.csv
│   ├── images/
│   └── ...
│
├── screenshots/
│
├── requirements.txt
└── README.md
```

---

# 🛠️ Technology Stack

### AI

* Google Gemini 2.5 Flash
* Agentic AI
* Vision-Language Models

### Backend

* Python

### Data Processing

* Pandas
* NumPy

### Frontend

* Streamlit

### Image Processing

* Pillow

---



# 🔮 Roadmap

* Reflection Agent
* Multi-image Evidence Fusion
* Human-in-the-loop Review
* PDF Claim Reports
* Live Claim Processing
* Advanced Fraud Detection
* Temporal Damage Verification
* REST API Deployment

---

---

# 👨‍💻 Author

**Pranjal Tyagi**

AI & Machine Learning Engineer | B.Tech CSE (AI & DS)
---



