# PPD Clinical Intelligence Layer

Clinical trial enrollment delays cost ~$500k/day in late-phase oncology. This prototype shows how PPD's Clario+Datavant data assets can screen patients in 90 seconds vs. 3 weeks of manual chart review.

![Screen 2: Analysis output with Clario provenance line](docs/screen2_screenshot.png)
*(Screenshot: Screen 2 analysis output for a high-risk patient, with Clario provenance line highlighted)*

## What it does

A 3-screen Streamlit demo that ingests a synthetic FHIR patient bundle against a real trial protocol (NCT04736745, KEYNOTE-590 Phase III), returns a criterion-by-criterion eligibility verdict, a retention risk score grounded in Clario cardiac endpoint history, and Datavant-powered site match recommendations.

**The differentiator:** Every data source is traceable to a PPD-proprietary asset a competitor cannot license.

> *"Cardiac endpoint signal from Clario trial database (n=10,000+ trials) — not available to generic AI tools."*

## Tech stack

- Python 3.10 / Streamlit 1.31+ (`st.write_stream()` for LLM streaming)
- OpenAI API (`gpt-4o`, streaming with pre-recorded fallback — demo cannot break)
- FHIR R4 synthetic patient JSON bundles with custom `ppd.com/fhir/ext/data-source` extension
- NCT04736745 real eligibility criteria (QTc >470ms exclusion criterion)

## Run locally

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your OpenAI API key to .env
streamlit run app.py
```

## Production vision

- **Integrate Datavant tokenization** for real patient data linkage across 80,000+ US care sites
- **Validate retention risk scores** against Clario trial outcome data (10,000+ trials with endpoint history)
- **Embed into PPD's eTMF** as an active screening intelligence layer — eligibility verdict at the point of referral, not 3 weeks later

## Why only PPD can build this

IQVIA has volume (1.2B records). Generic AI tools have reasoning. Only PPD has Clario's cardiac safety signal depth from 10,000+ actual trial endpoints combined with Datavant's privacy-protected cross-site linkage. That combination produces retention risk predictions no other CRO can offer.

---

*Built in 2 hours as an interview demo. The 2-hour build is the proof of concept; the 18-month vision is the business case.*
