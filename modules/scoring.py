"""Student Success Score calculation engine with dynamic weight renormalization.

EduPredict AI - byteXL HacXLerate 2026 (Problem Statement 4 by KPMG in India)
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


# Default baseline prototype weights (sum to 1.0)
DEFAULT_WEIGHTS = {
    "academic_performance": 0.25,
    "attendance": 0.20,
    "lms_completion": 0.15,
    "placement_readiness": 0.20,
    "skills_assessment": 0.10,
    "engagement_feedback": 0.10,
}


def normalize_academic_pillar(row: pd.Series) -> Optional[float]:
    """Normalize academic performance to a 0-100 scale.
    
    Formula:
    - Base score combines CGPA (scaled to 100) and internal test percentage.
    - If both available: 70% CGPA + 30% internal test.
    - Backlogs apply a transparent penalty of 5 points per backlog.
    - Result clamped between 0 and 100.
    """
    cgpa = row.get("cgpa")
    internal = row.get("internal_test_pct")
    backlogs = row.get("backlogs", 0)
    if pd.isna(backlogs):
        backlogs = 0

    has_cgpa = not pd.isna(cgpa)
    has_internal = not pd.isna(internal)

    if not has_cgpa and not has_internal:
        return None

    if has_cgpa and has_internal:
        base = (float(cgpa) * 10.0 * 0.70) + (float(internal) * 0.30)
    elif has_cgpa:
        base = float(cgpa) * 10.0
    else:
        base = float(internal)

    penalty = float(backlogs) * 5.0
    score = max(0.0, min(100.0, base - penalty))
    return round(score, 1)


def normalize_attendance_pillar(row: pd.Series) -> Optional[float]:
    """Normalize attendance to a 0-100 scale.
    
    Combines general attendance (70%) and practical lab attendance (30%) if both exist.
    """
    att = row.get("attendance_pct")
    lab = row.get("lab_attendance_pct")

    has_att = not pd.isna(att)
    has_lab = not pd.isna(lab)

    if not has_att and not has_lab:
        return None

    if has_att and has_lab:
        score = (float(att) * 0.70) + (float(lab) * 0.30)
    elif has_att:
        score = float(att)
    else:
        score = float(lab)

    return round(float(np.clip(score, 0.0, 100.0)), 1)


def normalize_lms_pillar(row: pd.Series) -> Optional[float]:
    """Normalize LMS and digital assignment completion to 0-100 scale.
    
    Assignment completion (70%) + video watch completion (30%).
    """
    assign = row.get("lms_assignment_completion_pct")
    video = row.get("lms_video_watch_pct")

    has_assign = not pd.isna(assign)
    has_video = not pd.isna(video)

    if not has_assign and not has_video:
        return None

    if has_assign and has_video:
        score = (float(assign) * 0.70) + (float(video) * 0.30)
    elif has_assign:
        score = float(assign)
    else:
        score = float(video)

    return round(float(np.clip(score, 0.0, 100.0)), 1)


def normalize_placement_pillar(row: pd.Series) -> Optional[float]:
    """Normalize placement readiness to 0-100 scale.
    
    Combines aptitude score (50%) and mock interview score (50%).
    """
    apt = row.get("aptitude_score")
    mock = row.get("mock_interview_score")

    has_apt = not pd.isna(apt)
    has_mock = not pd.isna(mock)

    if not has_apt and not has_mock:
        return None

    if has_apt and has_mock:
        score = (float(apt) * 0.50) + (float(mock) * 0.50)
    elif has_apt:
        score = float(apt)
    else:
        score = float(mock)

    return round(float(np.clip(score, 0.0, 100.0)), 1)


def normalize_skills_pillar(row: pd.Series) -> Optional[float]:
    """Normalize technical skills assessment to 0-100 scale.
    
    Coding score (60%) + Technical MCQ (40%) + minor bonus for verified certifications (up to 6 pts).
    """
    coding = row.get("coding_score")
    mcq = row.get("technical_mcq_score")
    certs = row.get("certifications_count", 0)
    if pd.isna(certs):
        certs = 0

    has_coding = not pd.isna(coding)
    has_mcq = not pd.isna(mcq)

    if not has_coding and not has_mcq:
        return None

    if has_coding and has_mcq:
        base = (float(coding) * 0.60) + (float(mcq) * 0.40)
    elif has_coding:
        base = float(coding)
    else:
        base = float(mcq)

    bonus = min(6.0, float(certs) * 2.0)
    score = max(0.0, min(100.0, base + bonus))
    return round(score, 1)


def normalize_engagement_pillar(row: pd.Series) -> Optional[float]:
    """Normalize engagement and feedback to 0-100 scale.
    
    Mentor rating (1-5 normalized to 100; 50%), club participation (25%), feedback sentiment (25%).
    """
    mentor = row.get("mentor_rating")
    club = row.get("club_participation_score")
    sentiment = row.get("feedback_sentiment_pct")

    parts = []
    weights = []

    if not pd.isna(mentor):
        # Scale 1-5 to 0-100: (rating / 5.0) * 100
        mentor_norm = (float(mentor) / 5.0) * 100.0
        parts.append(mentor_norm)
        weights.append(0.50)

    if not pd.isna(club):
        parts.append(float(club))
        weights.append(0.25)

    if not pd.isna(sentiment):
        parts.append(float(sentiment))
        weights.append(0.25)

    if not parts:
        return None

    norm_w = [w / sum(weights) for w in weights]
    score = sum(p * w for p, w in zip(parts, norm_w))
    return round(float(np.clip(score, 0.0, 100.0)), 1)


def extract_student_pillars(row: pd.Series) -> Dict[str, Optional[float]]:
    """Extract and normalize all 6 indicator pillars for a single student row."""
    return {
        "academic_performance": normalize_academic_pillar(row),
        "attendance": normalize_attendance_pillar(row),
        "lms_completion": normalize_lms_pillar(row),
        "placement_readiness": normalize_placement_pillar(row),
        "skills_assessment": normalize_skills_pillar(row),
        "engagement_feedback": normalize_engagement_pillar(row),
    }


def calculate_student_score(
    row: pd.Series,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Calculate the transparent Student Success Score with dynamic weight re-normalization.
    
    Returns a dict with:
    - score: float (0-100) or np.nan if no valid indicators
    - completeness_pct: float
    - valid_pillars_count: int
    - pillars: dict of pillar values (or None)
    - effective_weights: dict of actual redistributed weights used
    - strongest_pillar: str or None
    - weakest_pillar: str or None
    - calculation_steps: detailed human-readable step-by-step breakdown
    """
    cfg_weights = weights or DEFAULT_WEIGHTS
    pillars = extract_student_pillars(row)

    valid_pillars = {k: v for k, v in pillars.items() if v is not None}
    valid_count = len(valid_pillars)
    completeness_pct = round((valid_count / len(DEFAULT_WEIGHTS)) * 100.0, 1)

    # If NO valid indicators exist, return NaN - NEVER invent or default to 0!
    if valid_count == 0:
        return {
            "score": np.nan,
            "completeness_pct": 0.0,
            "valid_pillars_count": 0,
            "pillars": pillars,
            "effective_weights": {k: 0.0 for k in DEFAULT_WEIGHTS},
            "strongest_pillar": None,
            "weakest_pillar": None,
            "calculation_steps": "No valid indicator data found for this student. Score unavailable.",
        }

    # Re-normalize weights among valid pillars so their sum equals 1.0 (100%)
    valid_weight_sum = sum(cfg_weights[k] for k in valid_pillars)
    if valid_weight_sum <= 0:
        # Fallback to equal weighting among valid pillars
        effective_weights = {k: 1.0 / valid_count for k in valid_pillars}
    else:
        effective_weights = {
            k: cfg_weights[k] / valid_weight_sum for k in valid_pillars
        }

    # Complete effective weights dict including 0.0 for missing
    all_effective_weights = {
        k: round(effective_weights.get(k, 0.0), 4) for k in DEFAULT_WEIGHTS
    }

    # Compute weighted sum
    composite_score = sum(valid_pillars[k] * effective_weights[k] for k in valid_pillars)
    composite_score = round(float(np.clip(composite_score, 0.0, 100.0)), 1)

    # Identify strongest and weakest indicators
    sorted_pillars = sorted(valid_pillars.items(), key=lambda item: item[1])
    weakest_pillar = sorted_pillars[0][0] if sorted_pillars else None
    strongest_pillar = sorted_pillars[-1][0] if sorted_pillars else None

    # Step-by-step explanation string
    steps = [
        f"Valid Indicators: {valid_count}/{len(DEFAULT_WEIGHTS)} ({completeness_pct}% complete)",
        "Weighted contributions:"
    ]
    for k, v in valid_pillars.items():
        w = effective_weights[k]
        contrib = v * w
        steps.append(f"  • {k.replace('_', ' ').title()}: {v:.1f} × {w*100:.1f}% = {contrib:.2f}")

    if valid_count < len(DEFAULT_WEIGHTS):
        missing_names = [k.replace('_', ' ').title() for k, v in pillars.items() if v is None]
        steps.append(f"Missing indicators ({', '.join(missing_names)}) were excluded; weights were re-normalized.")

    steps.append(f"Final Success Score = {composite_score:.1f} / 100.0")

    return {
        "score": composite_score,
        "completeness_pct": completeness_pct,
        "valid_pillars_count": valid_count,
        "pillars": pillars,
        "effective_weights": all_effective_weights,
        "strongest_pillar": strongest_pillar,
        "weakest_pillar": weakest_pillar,
        "calculation_steps": "\n".join(steps),
    }


def compute_dataset_scores(
    df: pd.DataFrame,
    weights: Optional[Dict[str, float]] = None
) -> pd.DataFrame:
    """Compute Student Success Scores and all pillar metrics across a DataFrame."""
    res_df = df.copy()

    scores = []
    completeness = []
    strongest = []
    weakest = []

    # Pillar columns
    acad_list = []
    att_list = []
    lms_list = []
    place_list = []
    skills_list = []
    eng_list = []

    for _, row in res_df.iterrows():
        calc = calculate_student_score(row, weights)
        scores.append(calc["score"])
        completeness.append(calc["completeness_pct"])
        strongest.append(calc["strongest_pillar"])
        weakest.append(calc["weakest_pillar"])

        pillars = calc["pillars"]
        acad_list.append(pillars.get("academic_performance"))
        att_list.append(pillars.get("attendance"))
        lms_list.append(pillars.get("lms_completion"))
        place_list.append(pillars.get("placement_readiness"))
        skills_list.append(pillars.get("skills_assessment"))
        eng_list.append(pillars.get("engagement_feedback"))

    res_df["success_score"] = scores
    res_df["data_completeness_pct"] = completeness
    res_df["strongest_pillar"] = strongest
    res_df["weakest_pillar"] = weakest

    res_df["pillar_academic"] = acad_list
    res_df["pillar_attendance"] = att_list
    res_df["pillar_lms"] = lms_list
    res_df["pillar_placement"] = place_list
    res_df["pillar_skills"] = skills_list
    res_df["pillar_engagement"] = eng_list

    return res_df
