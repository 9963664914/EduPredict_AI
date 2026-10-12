"""Data export, reporting, and methodology documentation generator.

EduPredict AI - byteXL HacXLerate 2026 (Problem Statement 4 by KPMG in India)
"""

import io
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd


METHODOLOGY_SUMMARY = """# EduPredict AI — Methodology, Assumptions & Limitations

### 1. Prototype Scope & Nature
EduPredict AI is an exploratory diagnostic tool built for byteXL HacXLerate 2026 (Problem Statement 4 by KPMG in India).
The **Student Success Score** and **Risk Support Indicators** are **transparent heuristic indicator metrics**, NOT validated predictive statistical models of academic failure or job placement outcomes. All insights require qualified human review by faculty advisors, department heads, and training & placement officers.

### 2. Indicator Pillars & Configurable Weights
The overall score (0–100) integrates 6 pillars with baseline weights:
- **Academic Performance (25%)**: Normalized CGPA (70%) + Internal Exam Average (30%) with explicit deduction (-5 pts/backlog).
- **Attendance (20%)**: Classroom Attendance (70%) + Practical Lab Attendance (30%).
- **LMS Engagement (15%)**: Assignment Submission Rate (70%) + Video Lecture Completion (30%).
- **Placement Readiness (20%)**: Quantitative Aptitude (50%) + Mock Technical/HR Interview (50%).
- **Skills Assessment (10%)**: Hands-on Coding Assessment (60%) + Technical MCQ (40%) + Certified Skills Bonus.
- **Engagement & Feedback (10%)**: Faculty Mentor Rating (50%) + Club Activities (25%) + Feedback Sentiment (25%).

### 3. Missing Data & Dynamic Weight Re-normalization
When a student has missing data for one or more pillars:
1. Available valid pillars are identified.
2. The prototype weights of the valid pillars are dynamically re-normalized so that their sum equals exactly 100%.
3. Data completeness percentage is computed and displayed alongside the score.
4. **Zero-filling prohibition**: Missing data is NEVER silently replaced with zero.
5. If **no valid indicators exist**, the score is marked as `Unavailable` (`NaN`), never zero.

### 4. Independent Academic & Placement Risk Evaluation
Academic support and Placement readiness are evaluated independently:
- **On track**: Key benchmarks met or exceeded.
- **Needs review**: Metrics borderline or slight downward trend detected.
- **Support recommended**: Severe attendance shortage, backlogs, low CGPA, or aptitude gaps.
- **Insufficient data**: Inadequate data available to reach a sound diagnostic conclusion.

### 5. Responsible AI, Privacy & Human-in-the-Loop Ethics
- **No Autonomous High-Stakes Actions**: Support flags are advisory triggers for counseling and mentorship, not disciplinary actions or automated disqualifications.
- **Data Privacy**: Student records must be secured, access-controlled, and audited in compliance with institutional guidelines and DPDP Act regulations.
- **Explainability**: Every flag provides exact factor reasons and practical remedial actions.
"""


def export_dataframe_to_csv(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to UTF-8 encoded CSV bytes for download."""
    return df.to_csv(index=False).encode("utf-8")


def get_academic_support_export(df: pd.DataFrame) -> pd.DataFrame:
    """Filter and prepare student records recommended for academic support."""
    if "academic_risk_status" not in df.columns:
        return pd.DataFrame()

    sub = df[df["academic_risk_status"].isin(["Support recommended", "Needs review"])].copy()
    cols = [
        c for c in [
            "student_id", "name", "department", "semester", "cgpa", "backlogs",
            "attendance_pct", "success_score", "academic_risk_status", "academic_risk_reasons"
        ] if c in sub.columns
    ]
    return sub[cols].sort_values(by="cgpa", ascending=True) if "cgpa" in sub.columns else sub[cols]


def get_placement_support_export(df: pd.DataFrame) -> pd.DataFrame:
    """Filter and prepare student records recommended for placement readiness support."""
    if "placement_risk_status" not in df.columns:
        return pd.DataFrame()

    sub = df[df["placement_risk_status"].isin(["Support recommended", "Needs review"])].copy()
    cols = [
        c for c in [
            "student_id", "name", "department", "semester", "aptitude_score",
            "mock_interview_score", "coding_score", "success_score",
            "placement_risk_status", "placement_risk_reasons"
        ] if c in sub.columns
    ]
    return sub[cols].sort_values(by="aptitude_score", ascending=True) if "aptitude_score" in sub.columns else sub[cols]


def get_comprehensive_export(df: pd.DataFrame) -> pd.DataFrame:
    """Export comprehensive student dataset with all calculated scores and explanations."""
    export_cols = [
        "student_id", "name", "department", "semester", "gender",
        "cgpa", "backlogs", "attendance_pct",
        "lms_assignment_completion_pct", "aptitude_score", "mock_interview_score",
        "coding_score", "mentor_rating", "data_completeness_pct",
        "success_score", "academic_risk_status", "placement_risk_status",
        "overall_support_flag", "student_segment", "strongest_pillar", "weakest_pillar"
    ]
    avail_cols = [c for c in export_cols if c in df.columns]
    return df[avail_cols]
