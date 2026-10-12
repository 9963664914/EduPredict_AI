"""Unit tests for Student Success Score calculation and weight re-normalization."""

import numpy as np
import pandas as pd
import pytest
from modules.scoring import (
    calculate_student_score,
    compute_dataset_scores,
    DEFAULT_WEIGHTS,
)


def test_complete_student_score():
    row = pd.Series({
        "cgpa": 8.0,
        "backlogs": 0,
        "internal_test_pct": 80.0,
        "attendance_pct": 80.0,
        "lab_attendance_pct": 80.0,
        "lms_assignment_completion_pct": 80.0,
        "lms_video_watch_pct": 80.0,
        "aptitude_score": 80.0,
        "mock_interview_score": 80.0,
        "coding_score": 80.0,
        "technical_mcq_score": 80.0,
        "certifications_count": 0,
        "mentor_rating": 4.0,  # 4/5 = 80%
        "club_participation_score": 80.0,
        "feedback_sentiment_pct": 80.0,
    })
    res = calculate_student_score(row)
    assert not np.isnan(res["score"])
    assert round(res["score"], 1) == 80.0
    assert res["completeness_pct"] == 100.0
    assert res["valid_pillars_count"] == 6


def test_missing_indicators_weight_renormalization():
    # Only academics and attendance are present
    row = pd.Series({
        "cgpa": 8.0,
        "backlogs": 0,
        "internal_test_pct": 80.0,
        "attendance_pct": 90.0,
        "lab_attendance_pct": 90.0,
        # Rest are missing (NaN)
        "lms_assignment_completion_pct": np.nan,
        "aptitude_score": np.nan,
        "coding_score": np.nan,
        "mentor_rating": np.nan,
    })
    res = calculate_student_score(row)
    assert not np.isnan(res["score"])
    assert res["completeness_pct"] == round((2 / 6) * 100.0, 1)

    # Base weights: academic=0.25, attendance=0.20 -> sum=0.45
    # Normalized weights: academic = 0.25/0.45 (~0.5556), attendance = 0.20/0.45 (~0.4444)
    eff_w = res["effective_weights"]
    assert pytest.approx(eff_w["academic_performance"] + eff_w["attendance"], 0.01) == 1.0
    assert eff_w["lms_completion"] == 0.0


def test_unavailable_score_when_all_missing():
    row = pd.Series({
        "student_id": "STU999",
        "name": "Ghost Student",
        "cgpa": np.nan,
        "attendance_pct": np.nan,
        "lms_assignment_completion_pct": np.nan,
        "aptitude_score": np.nan,
        "coding_score": np.nan,
        "mentor_rating": np.nan,
    })
    res = calculate_student_score(row)
    # MUST return NaN, NEVER default to zero!
    assert np.isnan(res["score"])
    assert res["completeness_pct"] == 0.0
    assert res["valid_pillars_count"] == 0


def test_score_range_boundaries():
    min_row = pd.Series({
        "cgpa": 0.0,
        "backlogs": 10,
        "internal_test_pct": 0.0,
        "attendance_pct": 0.0,
        "lms_assignment_completion_pct": 0.0,
        "aptitude_score": 0.0,
        "coding_score": 0.0,
        "mentor_rating": 1.0,
    })
    min_res = calculate_student_score(min_row)
    assert min_res["score"] >= 0.0

    max_row = pd.Series({
        "cgpa": 10.0,
        "backlogs": 0,
        "internal_test_pct": 100.0,
        "attendance_pct": 100.0,
        "lab_attendance_pct": 100.0,
        "lms_assignment_completion_pct": 100.0,
        "aptitude_score": 100.0,
        "mock_interview_score": 100.0,
        "coding_score": 100.0,
        "technical_mcq_score": 100.0,
        "certifications_count": 5,
        "mentor_rating": 5.0,
    })
    max_res = calculate_student_score(max_row)
    assert max_res["score"] <= 100.0
