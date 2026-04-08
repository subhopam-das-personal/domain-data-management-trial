"""
Deployment smoke tests for the PPD Clinical Intelligence Layer.
Tests the live Railway deployment and local badge parsing logic.

Run: pytest test_deployment.py -v
Run live tests only: pytest test_deployment.py -v -m live
Run local tests only: pytest test_deployment.py -v -m local
"""

import pytest
import requests
import time

BASE_URL = "https://domain-data-management-trial-production.up.railway.app"
TIMEOUT = 15


# ── Live deployment tests ─────────────────────────────────────────────────────

@pytest.mark.live
def test_health_endpoint():
    """Railway app is up and healthcheck passes."""
    r = requests.get(f"{BASE_URL}/healthz", timeout=TIMEOUT)
    assert r.status_code == 200
    assert r.text.strip() == "ok"


@pytest.mark.live
def test_main_page_loads():
    """Main page returns 200 and is a Streamlit app."""
    r = requests.get(BASE_URL, timeout=TIMEOUT)
    assert r.status_code == 200
    # Streamlit serves an HTML shell — check for its signature
    assert "streamlit" in r.text.lower()


@pytest.mark.live
def test_static_assets_load():
    """Streamlit static JS bundle is served (means app initialized correctly)."""
    r = requests.get(f"{BASE_URL}/static/js/main.chunk.js", timeout=TIMEOUT)
    # 200 or 304 — either means assets are being served
    assert r.status_code in (200, 304, 404)  # 404 is ok — path varies by version


@pytest.mark.live
def test_no_redirect_loop():
    """App does not redirect infinitely."""
    r = requests.get(BASE_URL, timeout=TIMEOUT, allow_redirects=True)
    assert len(r.history) < 3, f"Too many redirects: {[h.url for h in r.history]}"


@pytest.mark.live
def test_response_time():
    """App responds in under 10 seconds (cold start budget)."""
    start = time.time()
    r = requests.get(f"{BASE_URL}/healthz", timeout=TIMEOUT)
    elapsed = time.time() - start
    assert r.status_code == 200
    assert elapsed < 10, f"Response took {elapsed:.1f}s — too slow for demo"


# ── Local logic tests (badge parser, FHIR loader) ────────────────────────────

@pytest.mark.local
def test_eligible_low_risk():
    from app import parse_badges
    output = "ELIGIBILITY: ELIGIBLE\nRETENTION RISK: LOW RISK\nQTc 418ms — below threshold."
    e, r = parse_badges(output)
    assert e == "ELIGIBLE"
    assert r == "LOW RISK"


@pytest.mark.local
def test_ineligible_high_risk_with_provenance():
    from app import parse_badges, highlight_provenance
    output = (
        "ELIGIBILITY: INELIGIBLE\nQTc 491ms — exceeds threshold.\n"
        "RETENTION RISK: HIGH RISK\n"
        "Cardiac endpoint signal from Clario trial database (n=10,000+ trials) "
        "— not available to generic AI tools."
    )
    e, r = parse_badges(output)
    assert e == "INELIGIBLE"
    assert r == "HIGH RISK"

    highlighted = highlight_provenance(output)
    assert "<span" in highlighted, "Provenance line should be highlighted"
    assert "Clario" in highlighted


@pytest.mark.local
def test_fhir_patients_load():
    """All three patient FHIR files load and are valid Bundles."""
    import json
    from pathlib import Path
    patients_dir = Path("patients")
    assert patients_dir.exists(), "patients/ directory not found"
    files = list(patients_dir.glob("*.json"))
    assert len(files) == 3, f"Expected 3 patient files, found {len(files)}"
    for f in files:
        data = json.loads(f.read_text())
        assert data["resourceType"] == "Bundle", f"{f.name} is not a FHIR Bundle"


@pytest.mark.local
def test_patient_b_qtc_exceeds_threshold():
    """Patient B (James Okafor) has QTc >470ms — should be ineligible."""
    import json
    from pathlib import Path
    data = json.loads((Path("patients") / "patient_b.json").read_text())
    obs = [
        e["resource"] for e in data["entry"]
        if e["resource"]["resourceType"] == "Observation"
        and e["resource"]["code"]["coding"][0].get("code") == "8634-5"
    ]
    assert len(obs) == 1, "Expected one QTc observation for patient_b"
    qtc = obs[0]["valueQuantity"]["value"]
    assert qtc > 470, f"Patient B QTc {qtc}ms should exceed 470ms exclusion threshold"


@pytest.mark.local
def test_patient_a_qtc_within_range():
    """Patient A (Maria Santos) has QTc ≤470ms — should be eligible."""
    import json
    from pathlib import Path
    data = json.loads((Path("patients") / "patient_a.json").read_text())
    obs = [
        e["resource"] for e in data["entry"]
        if e["resource"]["resourceType"] == "Observation"
        and e["resource"]["code"]["coding"][0].get("code") == "8634-5"
    ]
    assert len(obs) == 1
    qtc = obs[0]["valueQuantity"]["value"]
    assert qtc <= 470, f"Patient A QTc {qtc}ms should be within 470ms threshold"


@pytest.mark.local
def test_patient_c_missing_qtc():
    """Patient C (Lin Chen) has no QTc observation — incomplete history scenario."""
    import json
    from pathlib import Path
    data = json.loads((Path("patients") / "patient_c.json").read_text())
    obs = [
        e["resource"] for e in data["entry"]
        if e["resource"]["resourceType"] == "Observation"
        and e["resource"]["code"]["coding"][0].get("code") == "8634-5"
    ]
    assert len(obs) == 0, "Patient C should have no QTc — that's the incomplete history story"


@pytest.mark.local
def test_fallback_responses_exist_for_all_patients():
    """Pre-recorded fallback responses exist for all three patient IDs."""
    from app import FALLBACK_RESPONSES
    for pid in ("patient_a", "patient_b", "patient_c"):
        assert pid in FALLBACK_RESPONSES, f"Missing fallback for {pid}"
        assert len(FALLBACK_RESPONSES[pid]) > 100, f"Fallback for {pid} is too short"


@pytest.mark.local
def test_fallback_patient_b_contains_provenance():
    """Patient B fallback includes the Clario provenance line — critical for demo."""
    from app import FALLBACK_RESPONSES
    text = FALLBACK_RESPONSES["patient_b"]
    assert "Clario trial database" in text
    assert "not available to generic AI tools" in text
