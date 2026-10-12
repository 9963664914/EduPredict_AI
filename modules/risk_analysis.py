"""Independent academic and placement risk assessment with transparent rule factors.

EduPredict AI - byteXL HacXLerate 2026 (Problem Statement 4 by KPMG in India)
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


# Configurable risk assessment thresholds
DEFAULT_RISK_THRESHOLDS = {
    # Academic thresholds
    "academic_cgpa_critical": 6.0,
    "academic_cgpa_warning": 7.0,
    "academic_attendance_critical": 65.0,
    "academic_attendance_warning": 75.0,
    "academic_backlogs_critical": 2,
    "academic_score_critical": 55.0,
    "academic_score_warning": 65.0,
    # Placement thresholds
    "placement_aptitude_critical": 50.0,
    "placement_aptitude_warning": 65.0,
    "placement_interview_critical": 50.0,
    "placement_interview_warning": 65.0,
    "placement_coding_critical": 45.0,
    "placement_coding_warning": 60.0,
    "placement_score_critical": 50.0,
    "placement_score_warning": 65.0,
}


def assess_student_academic_risk(
    row: pd.Series,
    thresholds: Optional[Dict[str, float]] = None
) -> Tuple[str, List[str]]:
    """Evaluate academic support need independently based on clear heuristic rules.
    
    Returns:
    - status: 'Support recommended' | 'Needs review' | 'On track' | 'Insufficient data'
    - reasons: list of explanatory factor strings
    """
    th = thresholds or DEFAULT_RISK_THRESHOLDS
    reasons: List[str] = []

    cgpa = row.get("cgpa")
    backlogs = row.get("backlogs")
    att = row.get("attendance_pct")
    acad_score = row.get("pillar_academic")

    has_cgpa = not pd.isna(cgpa)
    has_att = not pd.isna(att)
    has_acad = not pd.isna(acad_score)

    # Check for insufficient data
    if not has_cgpa and not has_att and not has_acad:
        return "Insufficient data", ["No academic or attendance records available to evaluate academic progress."]

    critical_reasons: List[str] = []
    review_reasons: List[str] = []

    # CGPA evaluation
    if has_cgpa:
        cgpa_val = float(cgpa)
        if cgpa_val < th["academic_cgpa_critical"]:
            critical_reasons.append(f"CGPA ({cgpa_val:.2f}) is below critical threshold of {th['academic_cgpa_critical']}")
        elif cgpa_val < th["academic_cgpa_warning"]:
            review_reasons.append(f"CGPA ({cgpa_val:.2f}) is below target threshold of {th['academic_cgpa_warning']}")

    # Backlog evaluation
    if not pd.isna(backlogs):
        b_val = int(backlogs)
        if b_val >= th["academic_backlogs_critical"]:
            critical_reasons.append(f"Active backlogs ({b_val}) exceed critical limit of {int(th['academic_backlogs_critical'])}")
        elif b_val > 0:
            review_reasons.append(f"Student has {b_val} active backlog requiring remedial action")

    # Attendance evaluation
    if has_att:
        att_val = float(att)
        if att_val < th["academic_attendance_critical"]:
            critical_reasons.append(f"Attendance ({att_val:.1f}%) is critically below mandatory {th['academic_attendance_critical']}%")
        elif att_val < th["academic_attendance_warning"]:
            review_reasons.append(f"Attendance ({att_val:.1f}%) is below recommended {th['academic_attendance_warning']}% guideline")

    # Composite academic score
    if has_acad:
        acad_val = float(acad_score)
        if acad_val < th["academic_score_critical"]:
            critical_reasons.append(f"Composite Academic Pillar score ({acad_val:.1f}/100) is in critical zone")
        elif acad_val < th["academic_score_warning"]:
            review_reasons.append(f"Composite Academic Pillar score ({acad_val:.1f}/100) requires monitoring")

    if critical_reasons:
        return "Support recommended", critical_reasons
    elif review_reasons:
        return "Needs review", review_reasons
    else:
        return "On track", ["Academic metrics and attendance meet or exceed benchmark standards."]


def assess_student_placement_risk(
    row: pd.Series,
    thresholds: Optional[Dict[str, float]] = None
) -> Tuple[str, List[str]]:
    """Evaluate placement readiness support independently based on transparent rules.
    
    Returns:
    - status: 'Support recommended' | 'Needs review' | 'On track' | 'Insufficient data'
    - reasons: list of explanatory factor strings
    """
    th = thresholds or DEFAULT_RISK_THRESHOLDS

    apt = row.get("aptitude_score")
    mock = row.get("mock_interview_score")
    coding = row.get("coding_score")
    place_score = row.get("pillar_placement")

    has_apt = not pd.isna(apt)
    has_mock = not pd.isna(mock)
    has_coding = not pd.isna(coding)
    has_place = not pd.isna(place_score)

    if not has_apt and not has_mock and not has_coding and not has_place:
        return "Insufficient data", ["No placement assessments, mock interview, or coding test data found."]

    critical_reasons: List[str] = []
    review_reasons: List[str] = []

    # Aptitude evaluation
    if has_apt:
        apt_val = float(apt)
        if apt_val < th["placement_aptitude_critical"]:
            critical_reasons.append(f"Aptitude test score ({apt_val:.1f}%) is below readiness threshold {th['placement_aptitude_critical']}%")
        elif apt_val < th["placement_aptitude_warning"]:
            review_reasons.append(f"Aptitude test score ({apt_val:.1f}%) is below competitive benchmark {th['placement_aptitude_warning']}%")

    # Mock Interview evaluation
    if has_mock:
        mock_val = float(mock)
        if mock_val < th["placement_interview_critical"]:
            critical_reasons.append(f"Mock interview performance ({mock_val:.1f}%) needs intensive coaching (<{th['placement_interview_critical']}%)")
        elif mock_val < th["placement_interview_warning"]:
            review_reasons.append(f"Mock interview performance ({mock_val:.1f}%) is below target {th['placement_interview_warning']}%")

    # Coding skills evaluation
    if has_coding:
        code_val = float(coding)
        if code_val < th["placement_coding_critical"]:
            critical_reasons.append(f"Coding test score ({code_val:.1f}%) indicates critical hands-on gaps (<{th['placement_coding_critical']}%)")
        elif code_val < th["placement_coding_warning"]:
            review_reasons.append(f"Coding test score ({code_val:.1f}%) needs further practice (<{th['placement_coding_warning']}%)")

    # Composite placement pillar
    if has_place:
        place_val = float(place_score)
        if place_val < th["placement_score_critical"]:
            critical_reasons.append(f"Overall Placement Pillar score ({place_val:.1f}/100) indicates significant risk")
        elif place_val < th["placement_score_warning"]:
            review_reasons.append(f"Overall Placement Pillar score ({place_val:.1f}/100) shows room for improvement")

    if critical_reasons:
        return "Support recommended", critical_reasons
    elif review_reasons:
        return "Needs review", review_reasons
    else:
        return "On track", ["Placement readiness benchmarks and technical assessments are on target."]


def compute_dataset_risks(
    df: pd.DataFrame,
    thresholds: Optional[Dict[str, float]] = None
) -> pd.DataFrame:
    """Compute independent academic and placement risk statuses and detailed reasons for all students."""
    res_df = df.copy()

    acad_statuses = []
    acad_reasons_list = []
    place_statuses = []
    place_reasons_list = []
    combined_flags = []

    for _, row in res_df.iterrows():
        a_status, a_reasons = assess_student_academic_risk(row, thresholds)
        p_status, p_reasons = assess_student_placement_risk(row, thresholds)

        acad_statuses.append(a_status)
        acad_reasons_list.append("; ".join(a_reasons))
        place_statuses.append(p_status)
        place_reasons_list.append("; ".join(p_reasons))

        # Overall combined support priority flag
        if a_status == "Insufficient data" and p_status == "Insufficient data":
            comb = "Insufficient Data"
        elif a_status == "Support recommended" and p_status == "Support recommended":
            comb = "Dual Support Needed"
        elif a_status == "Support recommended":
            comb = "Academic Support Priority"
        elif p_status == "Support recommended":
            comb = "Placement Support Priority"
        elif a_status == "Needs review" or p_status == "Needs review":
            comb = "Review Recommended"
        else:
            comb = "On Track"

        combined_flags.append(comb)

    res_df["academic_risk_status"] = acad_statuses
    res_df["academic_risk_reasons"] = acad_reasons_list
    res_df["placement_risk_status"] = place_statuses
    res_df["placement_risk_reasons"] = place_reasons_list
    res_df["overall_support_flag"] = combined_flags

    return res_df
