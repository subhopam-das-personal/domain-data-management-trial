"""
Unit tests for parse_badges() in app.py.
Run: pytest test_badge_parser.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import parse_badges


def test_eligible_low_risk():
    output = """ELIGIBILITY: ELIGIBLE

Patient meets all inclusion criteria. QTc 418ms — below threshold.

RETENTION RISK: LOW RISK

Strong adherence history. No comorbidities flagging dropout risk."""
    eligibility, risk = parse_badges(output)
    assert eligibility == "ELIGIBLE"
    assert risk == "LOW RISK"


def test_ineligible_high_risk():
    output = """ELIGIBILITY: INELIGIBLE

QTc 491ms — exceeds the 470ms exclusion threshold.

RETENTION RISK: HIGH RISK

Cardiac endpoint signal from Clario trial database (n=10,000+ trials)
— not available to generic AI tools. Elevated dropout risk from antiarrhythmic co-medication."""
    eligibility, risk = parse_badges(output)
    assert eligibility == "INELIGIBLE"
    assert risk == "HIGH RISK"


def test_eligible_medium_risk():
    output = "ELIGIBILITY: ELIGIBLE\nRETENTION RISK: MEDIUM RISK\nFragmented records."
    eligibility, risk = parse_badges(output)
    assert eligibility == "ELIGIBLE"
    assert risk == "MEDIUM RISK"


def test_case_insensitive():
    output = "Eligibility: eligible\nRetention Risk: low risk"
    eligibility, risk = parse_badges(output)
    assert eligibility == "ELIGIBLE"
    assert risk == "LOW RISK"


def test_no_badges_returns_none():
    output = "Unable to determine eligibility from available data."
    eligibility, risk = parse_badges(output)
    assert eligibility is None
    assert risk is None
