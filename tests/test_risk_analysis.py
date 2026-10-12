"""Unit tests for independent risk analysis, student segmentation, and recommendations."""

import numpy as np
import pandas as pd
import pytest
from modules.risk_analysis import (
    assess_student_academic_risk,
    assess_student_placement_risk,
    compute_dataset_risks,
)
from modules.segmentation import (
    classify_student_segment,
    compute_dataset_segments,
)
from modules.recommendations import (
    generate_student_recommendations,
)


def test_academic_risk_levels():
    # Critical risk
    crit_row = pd.Series({"cgpa": 5.2, "backlogs": 2, "attendance_pct": 60.0})
    status, reasons = assess_student_academic_risk(crit_row)
    assert status == "Support recommended"
    assert len(reasons) >= 2

    # Warning / Review
    rev_row = pd.Series({"cgpa": 6.8, "backlogs": 0, "attendance_pct": 72.0})
    status, reasons = assess_student_academic_risk(rev_row)
    assert status == "Needs review"

    # On Track
    good_row = pd.Series({"cgpa": 8.5, "backlogs": 0, "attendance_pct": 85.0})
    status, reasons = assess_student_academic_risk(good_row)
    assert status == "On track"

    # Insufficient data
    empty_row = pd.Series({"cgpa": np.nan, "attendance_pct": np.nan, "pillar_academic": np.nan})
    status, reasons = assess_student_academic_risk(empty_row)
    assert status == "Insufficient data"


def test_placement_risk_levels():
    crit_row = pd.Series({"aptitude_score": 42.0, "mock_interview_score": 45.0, "coding_score": 40.0})
    status, reasons = assess_student_placement_risk(crit_row)
    assert status == "Support recommended"

    good_row = pd.Series({"aptitude_score": 85.0, "mock_interview_score": 80.0, "coding_score": 75.0})
    status, reasons = assess_student_placement_risk(good_row)
    assert status == "On track"


def test_segmentation_precedence():
    # 1. Insufficient data precedence
    nan_row = pd.Series({"success_score": np.nan, "data_completeness_pct": 20.0})
    assert classify_student_segment(nan_row) == "Insufficient data"

    # 2. Multiple support needs precedence
    multi_row = pd.Series({
        "success_score": 45.0,
        "data_completeness_pct": 100.0,
        "academic_risk_status": "Support recommended",
        "placement_risk_status": "Support recommended",
    })
    assert classify_student_segment(multi_row) == "Multiple support needs"

    # 3. Low attendance, reasonable academics
    att_row = pd.Series({
        "success_score": 72.0,
        "data_completeness_pct": 100.0,
        "academic_risk_status": "Needs review",
        "placement_risk_status": "On track",
        "attendance_pct": 65.0,
        "cgpa": 8.2,
    })
    assert classify_student_segment(att_row) == "Low attendance, reasonable academics"

    # 4. Low academics, adequate attendance
    acad_row = pd.Series({
        "success_score": 58.0,
        "data_completeness_pct": 100.0,
        "academic_risk_status": "Support recommended",
        "placement_risk_status": "On track",
        "attendance_pct": 88.0,
        "cgpa": 5.4,
        "backlogs": 2,
    })
    assert classify_student_segment(acad_row) == "Low academics, adequate attendance"

    # 5. Strong academics, low placement readiness
    place_row = pd.Series({
        "success_score": 68.0,
        "data_completeness_pct": 100.0,
        "academic_risk_status": "On track",
        "placement_risk_status": "Support recommended",
        "cgpa": 9.1,
        "aptitude_score": 44.0,
        "mock_interview_score": 40.0,
    })
    assert classify_student_segment(place_row) == "Strong academics, low placement readiness"


def test_explainable_recommendations():
    row = pd.Series({
        "student_id": "STU001",
        "cgpa": 5.2,
        "backlogs": 2,
        "attendance_pct": 62.0,
        "lms_assignment_completion_pct": 55.0,
        "aptitude_score": 45.0,
        "mock_interview_score": 48.0,
        "coding_score": 42.0,
        "data_completeness_pct": 100.0,
        "success_score": 48.0,
    })
    recs = generate_student_recommendations(row)
    assert len(recs) >= 3
    # Check that recommendations provide trigger reasons citing data
    categories = [r["category"] for r in recs]
    assert "Attendance & Engagement" in categories
    assert "Academic Remediation" in categories
    assert "Placement Readiness" in categories

    for r in recs:
        assert "trigger_reason" in r
        assert len(r["trigger_reason"]) > 0
        assert "recommended_action" in r
