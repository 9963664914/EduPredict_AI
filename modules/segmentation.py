"""Student segmentation module with deterministic precedence classification rules.

EduPredict AI - byteXL HacXLerate 2026 (Problem Statement 4 by KPMG in India)
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


SEGMENT_DEFINITIONS = {
    "Insufficient data": {
        "description": "Critical indicators are missing (<35% completeness or score unavailable); profile cannot be reliably evaluated.",
        "color": "#94a3b8",
        "priority": 1,
    },
    "Multiple support needs": {
        "description": "Student flagged for both academic and placement/attendance support; highest intervention priority.",
        "color": "#ef4444",
        "priority": 2,
    },
    "Low attendance, reasonable academics": {
        "description": "Maintains good academic results despite poor attendance; risk of disengagement or attendance-shortage bar.",
        "color": "#f59e0b",
        "priority": 3,
    },
    "Low academics, adequate attendance": {
        "description": "Attends classes regularly but struggles with academic conceptual understanding or exam performance.",
        "color": "#f97316",
        "priority": 4,
    },
    "Strong academics, low placement readiness": {
        "description": "High CGPA/theory knowledge but lacks competitive aptitude, coding skills, or interview readiness.",
        "color": "#8b5cf6",
        "priority": 5,
    },
    "Strong performance across available indicators": {
        "description": "Excels across academics, attendance, technical skills, and placement preparation.",
        "color": "#10b981",
        "priority": 6,
    },
    "Moderate / Consistent progress": {
        "description": "Satisfactory, balanced progress across available metrics without acute risk triggers.",
        "color": "#06b6d4",
        "priority": 7,
    },
}


def classify_student_segment(row: pd.Series) -> str:
    """Classify a student into exactly one mutually-distinct segment using strict precedence.
    
    Precedence minimizes ambiguities and overlapping assignments:
    1. Insufficient data
    2. Multiple support needs
    3. Low attendance, reasonable academics
    4. Low academics, adequate attendance
    5. Strong academics, low placement readiness
    6. Strong performance across available indicators
    7. Moderate / Consistent progress
    """
    completeness = row.get("data_completeness_pct", 100.0)
    score = row.get("success_score")
    acad_risk = row.get("academic_risk_status", "On track")
    place_risk = row.get("placement_risk_status", "On track")

    cgpa = row.get("cgpa")
    att = row.get("attendance_pct")
    apt = row.get("aptitude_score")
    mock = row.get("mock_interview_score")
    backlogs = row.get("backlogs", 0)

    acad_pillar = row.get("pillar_academic")
    att_pillar = row.get("pillar_attendance")
    place_pillar = row.get("pillar_placement")

    # Rule 1: Insufficient Data (Highest precedence)
    if (pd.isna(score) or completeness < 35.0 or
        (acad_risk == "Insufficient data" and place_risk == "Insufficient data")):
        return "Insufficient data"

    # Rule 2: Multiple support needs
    if (acad_risk == "Support recommended" and place_risk == "Support recommended"):
        return "Multiple support needs"
    
    # Secondary multiple need check if explicit pillar drops
    if (not pd.isna(backlogs) and int(backlogs) >= 2 and
        not pd.isna(att) and float(att) < 65.0 and
        not pd.isna(apt) and float(apt) < 50.0):
        return "Multiple support needs"

    # Rule 3: Low attendance, reasonable academics
    has_att = not pd.isna(att)
    has_cgpa = not pd.isna(cgpa)
    if has_att and float(att) < 75.0:
        if (has_cgpa and float(cgpa) >= 7.0) or (not pd.isna(acad_pillar) and float(acad_pillar) >= 65.0):
            return "Low attendance, reasonable academics"

    # Rule 4: Low academics, adequate attendance
    if has_att and float(att) >= 75.0:
        if ((has_cgpa and float(cgpa) < 6.0) or
            (not pd.isna(backlogs) and int(backlogs) >= 2) or
            (not pd.isna(acad_pillar) and float(acad_pillar) < 55.0)):
            return "Low academics, adequate attendance"

    # Rule 5: Strong academics, low placement readiness
    is_strong_acad = (has_cgpa and float(cgpa) >= 7.5) or (not pd.isna(acad_pillar) and float(acad_pillar) >= 75.0)
    is_low_place = (
        place_risk == "Support recommended" or
        (not pd.isna(place_pillar) and float(place_pillar) < 60.0) or
        (not pd.isna(apt) and float(apt) < 55.0) or
        (not pd.isna(mock) and float(mock) < 50.0)
    )
    if is_strong_acad and is_low_place:
        return "Strong academics, low placement readiness"

    # Rule 6: Strong performance across available indicators
    is_high_score = not pd.isna(score) and float(score) >= 75.0
    att_ok = pd.isna(att) or float(att) >= 78.0
    place_ok = pd.isna(place_pillar) or float(place_pillar) >= 70.0
    acad_ok = pd.isna(acad_pillar) or float(acad_pillar) >= 75.0

    if is_high_score and att_ok and place_ok and acad_ok:
        return "Strong performance across available indicators"

    # Rule 7: Default fallback category
    return "Moderate / Consistent progress"


def compute_dataset_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Classify all students in dataset into distinct segments."""
    res_df = df.copy()
    segments = [classify_student_segment(row) for _, row in res_df.iterrows()]
    res_df["student_segment"] = segments
    return res_df


def get_segment_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate summary statistics per student segment."""
    if "student_segment" not in df.columns:
        return pd.DataFrame()

    total = len(df)
    stats = []

    for seg_name, meta in SEGMENT_DEFINITIONS.items():
        sub = df[df["student_segment"] == seg_name]
        count = len(sub)
        pct = round((count / total) * 100.0, 1) if total > 0 else 0.0
        avg_score = round(float(sub["success_score"].dropna().mean()), 1) if not sub["success_score"].dropna().empty else None

        stats.append({
            "segment": seg_name,
            "count": count,
            "percentage": pct,
            "average_score": avg_score,
            "description": meta["description"],
            "color": meta["color"],
        })

    return pd.DataFrame(stats)
