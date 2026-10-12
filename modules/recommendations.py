"""Rule-based explainable student intervention and recommendation engine.

EduPredict AI - byteXL HacXLerate 2026 (Problem Statement 4 by KPMG in India)
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


def generate_student_recommendations(row: pd.Series) -> List[Dict[str, Any]]:
    """Generate explainable, rule-based practical interventions for a student.
    
    Every recommendation cites the exact metric values and conditions that triggered it.
    No LLM fabrication; 100% auditable and practical.
    """
    recs: List[Dict[str, Any]] = []

    cgpa = row.get("cgpa")
    backlogs = row.get("backlogs")
    internal = row.get("internal_test_pct")
    att = row.get("attendance_pct")
    lms = row.get("lms_assignment_completion_pct")
    apt = row.get("aptitude_score")
    mock = row.get("mock_interview_score")
    coding = row.get("coding_score")
    completeness = row.get("data_completeness_pct", 100.0)
    score = row.get("success_score")

    # 1. Critical Data Verification (if data incomplete)
    if pd.isna(score) or completeness < 60.0:
        missing_fields = []
        if pd.isna(cgpa): missing_fields.append("Academics/CGPA")
        if pd.isna(att): missing_fields.append("Attendance")
        if pd.isna(lms): missing_fields.append("LMS Activities")
        if pd.isna(apt) or pd.isna(mock): missing_fields.append("Placement Assessments")
        if pd.isna(coding): missing_fields.append("Technical Skills")

        recs.append({
            "category": "Data Quality & Assessment Sync",
            "priority": "High",
            "title": "Complete Missing Profile Assessments & Data Sync",
            "trigger_reason": f"Profile completeness is currently {completeness:.1f}%. Missing data detected in: {', '.join(missing_fields) if missing_fields else 'Key pillars'}.",
            "recommended_action": "Schedule makeup diagnostic assessments for missing modules and check LMS/exam portal synchronization.",
            "expected_outcome": "Accurate, unpenalized Student Success Score and complete diagnostic clarity.",
        })

    # 2. Attendance Follow-Up
    if not pd.isna(att):
        att_val = float(att)
        if att_val < 65.0:
            recs.append({
                "category": "Attendance & Engagement",
                "priority": "Urgent",
                "title": "Mandatory Faculty Advisor Attendance Check-In & Action Plan",
                "trigger_reason": f"Overall attendance ({att_val:.1f}%) is below critical 65% university detention threshold.",
                "recommended_action": "Schedule immediate 1-on-1 advisor counseling, notify guardian, and establish bi-weekly attendance check-ins.",
                "expected_outcome": "Prevent exam debarment and restore attendance above the mandatory 75% cutoff.",
            })
        elif att_val < 75.0:
            recs.append({
                "category": "Attendance & Engagement",
                "priority": "Medium",
                "title": "Attendance Monitoring & Early Warning Check",
                "trigger_reason": f"Overall attendance ({att_val:.1f}%) is below recommended 75% guideline.",
                "recommended_action": "Set up automated weekly attendance notifications and identify any recurring scheduling or health conflicts.",
                "expected_outcome": "Sustain attendance above 75% before end-of-semester cutoff.",
            })

    # 3. Subject Tutoring & Backlog Remediation
    has_backlogs = not pd.isna(backlogs) and int(backlogs) > 0
    low_cgpa = not pd.isna(cgpa) and float(cgpa) < 6.5
    low_internal = not pd.isna(internal) and float(internal) < 55.0

    if has_backlogs or (low_cgpa and low_internal):
        backlog_count = int(backlogs) if not pd.isna(backlogs) else 0
        recs.append({
            "category": "Academic Remediation",
            "priority": "High" if backlog_count >= 2 or (not pd.isna(cgpa) and float(cgpa) < 5.5) else "Medium",
            "title": "Targeted Remedial Subject Tutoring & Backlog Clearance Plan",
            "trigger_reason": f"Student has {backlog_count} active backlog(s) and CGPA of {f'{float(cgpa):.2f}' if not pd.isna(cgpa) else 'N/A'}.",
            "recommended_action": "Pair student with a subject faculty mentor and peer study circle for specific backlog subjects; provide curated revision question banks.",
            "expected_outcome": "Clear pending backlogs during next supplementary cycle and elevate SGPA by 0.5+ points.",
        })

    # 4. LMS & Digital Learning Completion
    if not pd.isna(lms) and float(lms) < 70.0:
        lms_val = float(lms)
        recs.append({
            "category": "LMS & Assignments",
            "priority": "Medium",
            "title": "Structured Assignment Catch-Up Milestone Schedule",
            "trigger_reason": f"LMS assignment completion rate ({lms_val:.1f}%) falls short of 75% benchmark.",
            "recommended_action": "Assign weekly modular assignment deadlines with grace periods; track LMS login frequency.",
            "expected_outcome": "Improve continuous internal evaluation marks and bridge course homework backlog.",
        })

    # 5. Aptitude & Reasoning Skills
    if not pd.isna(apt) and float(apt) < 60.0:
        apt_val = float(apt)
        recs.append({
            "category": "Placement Readiness",
            "priority": "High" if apt_val < 50.0 else "Medium",
            "title": "Quantitative Aptitude & Logical Reasoning Practice Track",
            "trigger_reason": f"Placement aptitude test score ({apt_val:.1f}%) is below competitive placement threshold (65%).",
            "recommended_action": "Enroll in campus placement aptitude bootcamp; complete 30 daily timed practice sets on quantitative and logical reasoning.",
            "expected_outcome": "Pass preliminary company aptitude screening rounds with 70%+ percentile.",
        })

    # 6. Coding Skills Acceleration
    if not pd.isna(coding) and float(coding) < 55.0:
        code_val = float(coding)
        recs.append({
            "category": "Technical Skill Development",
            "priority": "High" if code_val < 45.0 else "Medium",
            "title": "Hands-on Data Structures & Coding Accelerator",
            "trigger_reason": f"Coding assessment score ({code_val:.1f}%) indicates practical implementation gaps.",
            "recommended_action": "Assign curated 50-problem foundational DSA problem roadmap (arrays, strings, search, sort); participate in weekly college coding contests.",
            "expected_outcome": "Achieve consistent passing scores on coding assessment filters for technical roles.",
        })

    # 7. Mock Interview & Soft Skills
    if not pd.isna(mock) and float(mock) < 60.0:
        mock_val = float(mock)
        recs.append({
            "category": "Interview Preparation",
            "priority": "High" if mock_val < 50.0 else "Medium",
            "title": "Mock Technical & HR Interview Simulation Clinic",
            "trigger_reason": f"Mock interview evaluation score ({mock_val:.1f}%) indicates need for communication and answer structuring practice.",
            "recommended_action": "Conduct two simulated 45-minute mock interviews using STAR technique; refine resume project bullet points.",
            "expected_outcome": "Increase confidence and interview performance score to 75%+.",
        })

    # 8. High Performer Enrichment (if student is doing great)
    if not recs and not pd.isna(score) and float(score) >= 78.0:
        recs.append({
            "category": "Advanced Enrichment & Leadership",
            "priority": "Low",
            "title": "Peer Mentorship Role & Tier-1 Placement Fast-Track",
            "trigger_reason": f"Student maintains high overall Success Score ({float(score):.1f}/100) with solid performance across indicators.",
            "recommended_action": "Invite student to serve as junior peer tutor; fast-track for national hackathons, research projects, and premium dream-tier placements.",
            "expected_outcome": "Maximize top-tier placement offers and foster peer leadership.",
        })

    # Fallback if no specific condition met
    if not recs:
        recs.append({
            "category": "Continuous Monitoring",
            "priority": "Low",
            "title": "Maintain Balanced Study Schedule & Skill Portfolio",
            "trigger_reason": "Performance across all monitored pillars remains steady within acceptable tolerances.",
            "recommended_action": "Continue regular coursework, stay updated on LMS tasks, and attend weekly placement prep sessions.",
            "expected_outcome": "Sustain consistent academic and career readiness progress.",
        })

    return recs


def generate_recommendations_summary(df: pd.DataFrame) -> Dict[str, int]:
    """Generate counts of interventions recommended across the entire dataset."""
    counts: Dict[str, int] = {}
    for _, row in df.iterrows():
        recs = generate_student_recommendations(row)
        for r in recs:
            title = r["title"]
            counts[title] = counts.get(title, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))
