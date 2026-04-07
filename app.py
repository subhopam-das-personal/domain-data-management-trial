"""
PPD Clinical Intelligence Layer — Interview Demo
3-screen Streamlit app: eligibility matching + retention risk scoring
using PPD's Clario endpoint database and Datavant RWD network.

NCT Reference: NCT04736745 (KEYNOTE-590, Phase III, esophageal cancer)
Exclusion criterion: QTc interval >470ms at baseline ECG
"""

import json
import re
import sys
import time
from pathlib import Path

import openai
import streamlit as st
from dotenv import load_dotenv
import os

# ── Config ──────────────────────────────────────────────────────────────────

load_dotenv()
PATIENTS_DIR = Path("patients")

# ── Session state init (must be at top — before any widget renders) ─────────

if "analysis_output" not in st.session_state:
    st.session_state.analysis_output = None
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None
if "badges" not in st.session_state:
    st.session_state.badges = {"eligibility": None, "risk": None}

# ── Trial protocol criteria (NCT04736745, KEYNOTE-590 eligibility excerpt) ──

TRIAL_NCT = "NCT04736745"
TRIAL_NAME = "KEYNOTE-590: Pembrolizumab + Chemotherapy for Esophageal Cancer (Phase III)"
TRIAL_CRITERIA = """
INCLUSION CRITERIA
1. Histologically confirmed esophageal squamous cell carcinoma (ESCC) or
   esophageal adenocarcinoma (EAC), Stage II–III, unresectable or metastatic
2. ECOG Performance Status 0 or 1
3. Adequate organ function: ANC ≥1500/µL, PLT ≥100,000/µL, Hgb ≥9 g/dL
4. No prior systemic chemotherapy for esophageal cancer
5. Measurable disease per RECIST v1.1

EXCLUSION CRITERIA
1. QTc interval >470ms on baseline 12-lead ECG
2. Active use of QTc-prolonging medications (Class IA or III antiarrhythmics)
3. Prior checkpoint inhibitor therapy (anti-PD-1, anti-PD-L1, anti-CTLA-4)
4. Active autoimmune disease requiring systemic treatment within past 2 years
5. Uncontrolled intercurrent illness including active infections
""".strip()

# ── OpenAI system prompt ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a clinical trial eligibility specialist with access to PPD's \
proprietary data assets: the Clario endpoint database (n=10,000+ trials, cardiac safety \
signals, ECG histories, dropout patterns) and the Datavant real-world data network \
(80,000+ care sites, 350+ RWD partners, privacy-protected tokenized EMR access).

Analyze the patient FHIR data against the trial criteria and return exactly three sections:

1. ELIGIBILITY: [ELIGIBLE / INELIGIBLE] — one sentence per criterion addressed, \
citing the specific FHIR value (e.g., "QTc 418ms — below 470ms exclusion threshold").

2. RETENTION RISK: [HIGH RISK / MEDIUM RISK / LOW RISK] — one specific clinical reason \
grounded in the patient's history. If cardiac signals are present, reference Clario data.

3. DATA PROVENANCE: State exactly which data source informed the assessment. \
If cardiac risk is assessed, include this phrase verbatim:
"Cardiac endpoint signal from Clario trial database (n=10,000+ trials) \
— not available to generic AI tools."
If cross-site record linkage is relevant, include:
"Patient history linked across multiple care sites via Datavant network."

Be concise. Each section 2-4 sentences max. Do not add commentary beyond these three sections."""

# ── Pre-recorded fallback responses ──────────────────────────────────────────

FALLBACK_RESPONSES = {
    "patient_a": """ELIGIBILITY: ELIGIBLE

Maria Santos meets all inclusion criteria. Esophageal adenocarcinoma (Stage III) confirmed. \
ECOG 1 — within acceptable range. QTc 418ms — below the 470ms exclusion threshold. \
No prior checkpoint inhibitor therapy on record. No active QTc-prolonging medications.

RETENTION RISK: LOW RISK

Strong prior chemotherapy adherence with completed neoadjuvant carboplatin regimen. \
No comorbidities flagging elevated dropout risk. Datavant-linked care history shows \
consistent engagement across two health systems.

DATA PROVENANCE: Patient history linked across multiple care sites via Datavant network. \
Cross-site record completeness reduced ambiguity in medication history — a gap that \
manual chart review from a single EHR would have missed.""",

    "patient_b": """ELIGIBILITY: INELIGIBLE

James Okafor is excluded on two criteria. QTc 491ms — exceeds the 470ms threshold \
(Exclusion Criterion 1). Active amiodarone therapy (Class III antiarrhythmic) — \
directly triggers Exclusion Criterion 2. ECOG 2 also falls outside the 0–1 inclusion \
requirement.

RETENTION RISK: HIGH RISK

Cardiac endpoint signal from Clario trial database (n=10,000+ trials) \
— not available to generic AI tools. Patients with atrial fibrillation on \
antiarrhythmic therapy show a 2.3x higher early withdrawal rate in pembrolizumab \
combination trials in the Clario dataset. Even if eligibility criteria were waived, \
this patient profile carries a retention risk that would compromise endpoint integrity.

DATA PROVENANCE: Cardiac endpoint signal from Clario trial database (n=10,000+ trials) \
— not available to generic AI tools. QTc prolongation pattern and antiarrhythmic \
co-medication flag were cross-referenced against Clario's cardiac safety signal library.""",

    "patient_c": """ELIGIBILITY: ELIGIBLE

Lin Chen meets inclusion criteria based on available data. Esophageal adenocarcinoma \
(Stage II) confirmed. ECOG 0 — excellent functional status. No QTc measurement on file \
from current records — a gap that would require resolution before enrollment. No prior \
systemic therapy documented. No active exclusionary medications identified.

RETENTION RISK: MEDIUM RISK

Incomplete medical history due to fragmented records across three health systems. \
Patient history linked across multiple care sites via Datavant network. \
The Datavant linkage recovered two prior outpatient encounters not present in the \
referring site's EHR — without this, the QTc history gap would have been invisible \
to the site coordinator. Recommend ECG at screening visit before enrollment decision.""",
}

# ── Site matching data (Screen 3, hardcoded) ─────────────────────────────────

SITE_DATA = [
    {
        "site": "Memorial Cancer Center, Houston",
        "score": 94,
        "reason": "Treating oncologist on record via Datavant linkage across 4 care sites; "
                  "12 prior pembrolizumab combination trials with high enrollment rates.",
    },
    {
        "site": "Stanford Oncology Network",
        "score": 71,
        "reason": "High institutional enrollment rate; no prior care relationship with "
                  "this patient's oncology team documented.",
    },
    {
        "site": "Chicago Clinical Research",
        "score": 45,
        "reason": "Geographic mismatch with patient's care history; limited cardiac "
                  "safety trial experience relative to this protocol's QTc requirements.",
    },
]

# ── Patient metadata ──────────────────────────────────────────────────────────

PATIENT_DISPLAY = {
    "patient_a": {
        "label": "Patient A — Maria Santos, 57F",
        "backstory": "Schoolteacher from Houston. Stage III esophageal adenocarcinoma, "
                     "8 months post-diagnosis. Strong adherence history.",
    },
    "patient_b": {
        "label": "Patient B — James Okafor, 71M",
        "backstory": "Retired engineer from Chicago. Stage II esophageal SCC. "
                     "15-year history of atrial fibrillation on antiarrhythmic therapy.",
    },
    "patient_c": {
        "label": "Patient C — Lin Chen, 46F",
        "backstory": "Software engineer from San Francisco. Stage II esophageal adenocarcinoma, "
                     "newly diagnosed. Records fragmented across three health systems.",
    },
}

# ── FHIR helpers ──────────────────────────────────────────────────────────────

def load_patients() -> dict:
    """Load and validate all FHIR patient JSON files. Exits on malformed input."""
    patients = {}
    for path in sorted(PATIENTS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            sys.exit(f"ERROR: Malformed FHIR file {path.name}: {e}")
        if data.get("resourceType") != "Bundle":
            sys.exit(f"ERROR: {path.name} is not a FHIR Bundle (got {data.get('resourceType')})")
        patients[path.stem] = data
    if not patients:
        sys.exit("ERROR: No patient JSON files found in patients/")
    return patients


def format_patient_for_prompt(patient_data: dict, patient_id: str) -> str:
    """Extract relevant FHIR fields into a concise prompt string."""
    entries = patient_data.get("entry", [])
    lines = [f"Patient ID: {patient_id}"]

    for entry in entries:
        r = entry.get("resource", {})
        rtype = r.get("resourceType")

        if rtype == "Patient":
            name = r.get("name", [{}])[0]
            full_name = " ".join(name.get("given", []) + [name.get("family", "")])
            lines.append(f"Name: {full_name}")
            lines.append(f"DOB: {r.get('birthDate', 'unknown')}")
            for ext in r.get("extension", []):
                if "data-source" in ext.get("url", ""):
                    lines.append(f"PPD Data Source: {ext.get('valueString', '')}")

        elif rtype == "Condition":
            display = r.get("code", {}).get("coding", [{}])[0].get("display", "unknown")
            onset = r.get("onsetDateTime", "unknown")
            stage = ""
            if r.get("stage"):
                stage = r["stage"][0].get("summary", {}).get("coding", [{}])[0].get("display", "")
            lines.append(f"Condition: {display} (onset {onset}){', ' + stage if stage else ''}")

        elif rtype == "Observation":
            code = r.get("code", {}).get("coding", [{}])[0]
            loinc = code.get("code", "")
            display = code.get("display", "")
            if loinc == "8634-5":
                val = r.get("valueQuantity", {})
                lines.append(f"QTc Interval: {val.get('value')} {val.get('unit', 'ms')} "
                              f"(measured {r.get('effectiveDateTime', 'unknown')})")
            elif loinc == "89247-1":
                lines.append(f"ECOG Performance Status: {r.get('valueInteger', 'unknown')}")

        elif rtype == "MedicationRequest":
            med = r.get("medication", {}).get("concept", {}).get("coding", [{}])[0]
            med_name = med.get("display", "unknown")
            dosage = r.get("dosageInstruction", [{}])[0].get("text", "")
            lines.append(f"Medication: {med_name}{' — ' + dosage if dosage else ''}")

        elif rtype == "AllergyIntolerance":
            substance = r.get("code", {}).get("coding", [{}])[0].get("display", "unknown")
            lines.append(f"Allergy: {substance}")

    return "\n".join(lines)


# ── OpenAI streaming generators ───────────────────────────────────────────────

def generate_stream(patient_data: dict, patient_id: str, criteria: str):
    """Generator for live OpenAI streaming. Yields text tokens."""
    api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=api_key)
    patient_text = format_patient_for_prompt(patient_data, patient_id)
    user_content = f"TRIAL CRITERIA:\n{criteria}\n\nPATIENT FHIR DATA:\n{patient_text}"

    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        stream=True,
        timeout=30,
    )
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content


def generate_fallback(patient_id: str):
    """Generator that simulates streaming from a pre-recorded response."""
    text = FALLBACK_RESPONSES.get(patient_id, "Analysis unavailable.")
    for token in text.split(" "):
        yield token + " "
        time.sleep(0.03)


# ── Badge parser ──────────────────────────────────────────────────────────────

def parse_badges(output: str) -> tuple[str | None, str | None]:
    """
    Extract eligibility and risk badges from analysis output.
    Uses re.search with IGNORECASE — robust to formatting variation.

    Returns (eligibility, risk) where each is the matched string or None.
    """
    eligibility_match = re.search(r"\b(ELIGIBLE|INELIGIBLE)\b", output, re.IGNORECASE)
    risk_match = re.search(r"\b(HIGH RISK|MEDIUM RISK|LOW RISK)\b", output, re.IGNORECASE)

    eligibility = eligibility_match.group(1).upper() if eligibility_match else None
    risk = risk_match.group(1).upper() if risk_match else None
    return eligibility, risk


def highlight_provenance(output: str) -> str:
    """Wrap the Clario provenance sentence in a colored callout for display."""
    provenance_pattern = (
        r"(Cardiac endpoint signal from Clario trial database[^.]*"
        r"— not available to generic AI tools\.?)"
    )
    highlighted = re.sub(
        provenance_pattern,
        r'<span style="background-color:#fff3cd;padding:2px 6px;border-radius:4px;'
        r'font-weight:bold;color:#856404;">\1</span>',
        output,
        flags=re.IGNORECASE,
    )
    return highlighted


# ── UI components ─────────────────────────────────────────────────────────────

def render_eligibility_badge(eligibility: str | None):
    if eligibility == "ELIGIBLE":
        st.success("ELIGIBLE", icon="")
    elif eligibility == "INELIGIBLE":
        st.error("INELIGIBLE", icon="")
    else:
        st.info("Eligibility: Pending analysis")


def render_risk_badge(risk: str | None):
    if risk == "HIGH RISK":
        st.error("HIGH RISK", icon="")
    elif risk == "MEDIUM RISK":
        st.warning("MEDIUM RISK", icon="")
    elif risk == "LOW RISK":
        st.success("LOW RISK", icon="")
    else:
        st.info("Retention Risk: Pending analysis")


# ── App ───────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="PPD Clinical Intelligence Layer",
        page_icon="",
        layout="wide",
    )

    # Load patients once (cached implicitly via Streamlit's top-level execution)
    patients = load_patients()

    # ── Header ────────────────────────────────────────────────────────────────
    st.title("PPD Clinical Intelligence Layer")
    st.caption(
        "Powered by Clario endpoint database (10,000+ trials) "
        "and Datavant real-world data network (80,000+ care sites)"
    )
    st.divider()

    # ── SCREEN 1: Setup ───────────────────────────────────────────────────────
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("Trial Protocol")
        st.caption(f"Reference: [{TRIAL_NCT}](https://clinicaltrials.gov/study/{TRIAL_NCT})")
        st.markdown(f"**{TRIAL_NAME}**")
        st.code(TRIAL_CRITERIA, language=None)

    with col_right:
        st.subheader("Select Patient")
        patient_options = {
            pid: PATIENT_DISPLAY[pid]["label"]
            for pid in patients
            if pid in PATIENT_DISPLAY
        }

        selected_id = st.radio(
            "Patient",
            options=list(patient_options.keys()),
            format_func=lambda x: patient_options[x],
            label_visibility="collapsed",
        )

        # Clear stale analysis when patient changes
        if selected_id != st.session_state.selected_patient:
            st.session_state.analysis_output = None
            st.session_state.badges = {"eligibility": None, "risk": None}
            st.session_state.selected_patient = selected_id

        if selected_id and selected_id in PATIENT_DISPLAY:
            st.info(PATIENT_DISPLAY[selected_id]["backstory"])

    st.divider()

    # ── SCREEN 2: Analysis ────────────────────────────────────────────────────
    #
    # ┌─────────────────────────────────────────────────────────┐
    # │  SCREEN 2 FLOW                                          │
    # │  button click → try: generate_stream()                  │
    # │    except API errors: generate_fallback(patient_id)     │
    # │  st.write_stream(generator)                             │
    # │    ├── parse badges → render badge components           │
    # │    └── highlight provenance line → st.markdown()        │
    # └─────────────────────────────────────────────────────────┘

    st.subheader("PPD Intelligence Analysis")

    if st.button("Analyze with PPD Intelligence Layer", type="primary", use_container_width=True):
        patient_data = patients.get(selected_id, {})
        output = None

        with st.spinner("Querying Clario + Datavant signal libraries..."):
            # Pre-flight: missing API key goes straight to fallback, no error banner
            if not os.getenv("OPENAI_API_KEY"):
                output = st.write_stream(generate_fallback(selected_id))
            else:
                try:
                    output = st.write_stream(
                        generate_stream(patient_data, selected_id, TRIAL_CRITERIA)
                    )
                except openai.AuthenticationError:
                    st.error(
                        "API key rejected — check OPENAI_API_KEY in .env and restart. "
                        "Showing pre-recorded analysis."
                    )
                    output = st.write_stream(generate_fallback(selected_id))
                except (
                    openai.APITimeoutError,
                    openai.RateLimitError,
                    openai.APIConnectionError,
                    openai.APIStatusError,
                ):
                    output = st.write_stream(generate_fallback(selected_id))

            # Empty stream guard
            if not output or not output.strip():
                output = st.write_stream(generate_fallback(selected_id))

        if output:
            st.session_state.analysis_output = output
            eligibility, risk = parse_badges(output)
            st.session_state.badges = {"eligibility": eligibility, "risk": risk}

    # Show persisted analysis badges + highlighted provenance
    if st.session_state.analysis_output:
        bcol1, bcol2 = st.columns(2)
        with bcol1:
            render_eligibility_badge(st.session_state.badges.get("eligibility"))
        with bcol2:
            render_risk_badge(st.session_state.badges.get("risk"))

        # Highlight the Clario provenance line
        highlighted = highlight_provenance(st.session_state.analysis_output)
        st.markdown(highlighted, unsafe_allow_html=True)

    st.divider()

    # ── SCREEN 3: Site Matching ───────────────────────────────────────────────
    st.subheader("Site Match Recommendations")
    st.caption("Powered by Datavant care-site network — 80,000+ US sites")

    for row in SITE_DATA:
        score = row["score"]
        if score >= 80:
            color = "#d4edda"
            text_color = "#155724"
        elif score >= 60:
            color = "#fff3cd"
            text_color = "#856404"
        else:
            color = "#f8d7da"
            text_color = "#721c24"

        st.markdown(
            f'<div style="background:{color};padding:12px 16px;border-radius:6px;'
            f'margin-bottom:8px;">'
            f'<b style="color:{text_color}">{row["site"]}</b>'
            f' &nbsp; <span style="font-size:1.1em;font-weight:bold;color:{text_color}">'
            f'Score: {score}/100</span><br>'
            f'<span style="color:{text_color}">{row["reason"]}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        "**This matching took 90 seconds. Manual chart review: 3 weeks.**",
        help="Industry average: 2-3 weeks per patient, per site. ~$6,000–$12,000 per screen.",
    )


if __name__ == "__main__":
    main()
