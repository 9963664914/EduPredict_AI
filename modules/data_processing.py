"""Data processing, schema validation, synthetic data generation, and CSV merging module.

EduPredict AI - byteXL HacXLerate 2026 (Problem Statement 4 by KPMG in India)
"""

import os
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


# Schema definition with data types and valid numeric boundaries
FEATURE_SCHEMA = {
    # Demographics
    "student_id": {"type": "string", "required": True},
    "name": {"type": "string", "required": True},
    "department": {"type": "string", "required": True},
    "semester": {"type": "string", "required": True},
    "gender": {"type": "string", "required": False},
    # Academic Indicators
    "cgpa": {"type": "float", "min": 0.0, "max": 10.0, "required": False},
    "backlogs": {"type": "int", "min": 0, "max": 20, "required": False},
    "internal_test_pct": {"type": "float", "min": 0.0, "max": 100.0, "required": False},
    # Attendance Indicators
    "attendance_pct": {"type": "float", "min": 0.0, "max": 100.0, "required": False},
    "lab_attendance_pct": {"type": "float", "min": 0.0, "max": 100.0, "required": False},
    # LMS Indicators
    "lms_assignment_completion_pct": {"type": "float", "min": 0.0, "max": 100.0, "required": False},
    "lms_video_watch_pct": {"type": "float", "min": 0.0, "max": 100.0, "required": False},
    "lms_login_frequency_per_week": {"type": "float", "min": 0.0, "max": 30.0, "required": False},
    # Placement Readiness
    "aptitude_score": {"type": "float", "min": 0.0, "max": 100.0, "required": False},
    "mock_interview_score": {"type": "float", "min": 0.0, "max": 100.0, "required": False},
    "placement_registered": {"type": "string", "required": False},
    # Skills Assessment
    "coding_score": {"type": "float", "min": 0.0, "max": 100.0, "required": False},
    "technical_mcq_score": {"type": "float", "min": 0.0, "max": 100.0, "required": False},
    "certifications_count": {"type": "int", "min": 0, "max": 15, "required": False},
    # Engagement and Feedback
    "mentor_rating": {"type": "float", "min": 1.0, "max": 5.0, "required": False},
    "club_participation_score": {"type": "float", "min": 0.0, "max": 100.0, "required": False},
    "feedback_sentiment_pct": {"type": "float", "min": 0.0, "max": 100.0, "required": False},
}

# The 6 core indicator pillars for student success evaluation
CORE_PILLARS = [
    "academic_performance",
    "attendance",
    "lms_completion",
    "placement_readiness",
    "skills_assessment",
    "engagement_feedback",
]


def generate_synthetic_dataset(num_students: int = 100, seed: int = 42) -> pd.DataFrame:
    """Generate a realistic, deterministic synthetic dataset of fictional students.
    
    Includes diverse departments, balanced gender distributions, realistic academic
    spread, and explicit edge cases (e.g. high academic but low placement, low attendance
    with decent CGPA, multi-risk students, incomplete records).
    """
    np.random.seed(seed)

    departments = [
        "Computer Science",
        "Information Technology",
        "Electronics & Comm",
        "Mechanical",
        "Data Science & AI",
    ]
    semesters = ["Semester 4", "Semester 6", "Semester 8"]
    first_names = [
        "Aarav", "Aditi", "Ananya", "Arjun", "Bhavna", "Chirag", "Divya", "Farhan",
        "Gauri", "Harsh", "Ishaan", "Jaya", "Karan", "Kavya", "Manish", "Neha",
        "Nikhil", "Pooja", "Pranav", "Priya", "Rahul", "Rhea", "Rohan", "Sanjana",
        "Siddharth", "Sneha", "Tanvi", "Varun", "Vikram", "Zoya", "Ayush", "Meera",
        "Ritik", "Shreya", "Kabir", "Simran", "Deepak", "Swati", "Mohit", "Anjali"
    ]
    last_names = [
        "Sharma", "Verma", "Patel", "Reddy", "Nair", "Iyer", "Gupta", "Singh",
        "Mehta", "Rao", "Kumar", "Das", "Joshi", "Bose", "Chopra", "Chatterjee",
        "Pandey", "Mishra", "Deshmukh", "Pillai", "Kulkarni", "Aggarwal", "Chauhan"
    ]

    records: List[Dict[str, Any]] = []

    for i in range(1, num_students + 1):
        s_id = f"STU{i:04d}"
        fn = first_names[(i * 3 + 7) % len(first_names)]
        ln = last_names[(i * 5 + 11) % len(last_names)]
        name = f"{fn} {ln}"
        gender = "Female" if (i % 2 == 0) else "Male"
        dept = departments[i % len(departments)]
        sem = semesters[i % len(semesters)]

        # Base distributions
        cgpa = round(np.clip(np.random.normal(7.4, 1.2), 3.5, 9.9), 2)
        backlogs = int(np.random.choice([0, 1, 2, 3, 4], p=[0.72, 0.16, 0.07, 0.03, 0.02]))
        internal_pct = round(np.clip(cgpa * 9.5 + np.random.normal(0, 5), 35.0, 98.0), 1)

        attendance = round(np.clip(np.random.normal(78.0, 12.0), 38.0, 99.0), 1)
        lab_attendance = round(np.clip(attendance + np.random.normal(2.0, 5.0), 35.0, 100.0), 1)

        lms_completion = round(np.clip(np.random.normal(75.0, 15.0), 20.0, 100.0), 1)
        lms_video = round(np.clip(lms_completion + np.random.normal(-3.0, 8.0), 15.0, 99.0), 1)
        lms_logins = round(np.clip(np.random.normal(6.5, 2.5), 1.0, 16.0), 1)

        aptitude = round(np.clip(np.random.normal(68.0, 15.0), 25.0, 98.0), 1)
        mock_interview = round(np.clip(np.random.normal(65.0, 16.0), 20.0, 96.0), 1)
        placement_reg = "Yes" if (sem in ["Semester 6", "Semester 8"] and np.random.rand() > 0.1) else "No"

        coding = round(np.clip(np.random.normal(66.0, 18.0), 20.0, 99.0), 1)
        tech_mcq = round(np.clip(np.random.normal(70.0, 14.0), 25.0, 95.0), 1)
        certs = int(np.random.choice([0, 1, 2, 3, 4, 5], p=[0.25, 0.35, 0.22, 0.12, 0.04, 0.02]))

        mentor_rating = round(np.clip(np.random.normal(3.8, 0.7), 1.5, 5.0), 1)
        club_participation = round(np.clip(np.random.normal(60.0, 20.0), 10.0, 100.0), 1)
        sentiment_pct = round(np.clip(np.random.normal(72.0, 14.0), 25.0, 98.0), 1)

        # Inject specific edge cases at deterministic indices
        # Edge Case 1: Strong academics, low placement readiness (indices 10 to 14)
        if 10 <= i <= 14:
            cgpa = round(float(np.random.uniform(8.7, 9.8)), 2)
            backlogs = 0
            internal_pct = round(float(np.random.uniform(88.0, 96.0)), 1)
            aptitude = round(float(np.random.uniform(32.0, 48.0)), 1)
            mock_interview = round(float(np.random.uniform(28.0, 46.0)), 1)
            coding = round(float(np.random.uniform(35.0, 52.0)), 1)
            attendance = round(float(np.random.uniform(84.0, 95.0)), 1)

        # Edge Case 2: Low attendance, reasonable academics (indices 20 to 24)
        elif 20 <= i <= 24:
            attendance = round(float(np.random.uniform(52.0, 68.0)), 1)
            lab_attendance = round(float(np.random.uniform(50.0, 70.0)), 1)
            cgpa = round(float(np.random.uniform(7.4, 8.6)), 2)
            backlogs = 0
            internal_pct = round(float(np.random.uniform(72.0, 85.0)), 1)

        # Edge Case 3: Low academics, adequate attendance (indices 30 to 34)
        elif 30 <= i <= 34:
            cgpa = round(float(np.random.uniform(4.0, 5.4)), 2)
            backlogs = int(np.random.choice([2, 3, 4]))
            internal_pct = round(float(np.random.uniform(40.0, 54.0)), 1)
            attendance = round(float(np.random.uniform(82.0, 94.0)), 1)
            lab_attendance = round(float(np.random.uniform(80.0, 95.0)), 1)

        # Edge Case 4: Multiple support needs (indices 40 to 44)
        elif 40 <= i <= 44:
            cgpa = round(float(np.random.uniform(3.8, 5.2)), 2)
            backlogs = int(np.random.choice([2, 3, 5]))
            attendance = round(float(np.random.uniform(44.0, 64.0)), 1)
            aptitude = round(float(np.random.uniform(30.0, 45.0)), 1)
            mock_interview = round(float(np.random.uniform(25.0, 42.0)), 1)
            coding = round(float(np.random.uniform(22.0, 40.0)), 1)

        # Edge Case 5: Missing placement data (indices 50 to 52)
        elif 50 <= i <= 52:
            aptitude = np.nan
            mock_interview = np.nan
            placement_reg = "No"

        # Edge Case 6: Missing LMS & Skills data (indices 60 to 61)
        elif 60 <= i <= 61:
            lms_completion = np.nan
            lms_video = np.nan
            coding = np.nan
            technical_mcq = np.nan

        # Edge Case 7: High performer across all metrics (indices 70 to 74)
        elif 70 <= i <= 74:
            cgpa = round(float(np.random.uniform(9.1, 9.8)), 2)
            backlogs = 0
            attendance = round(float(np.random.uniform(90.0, 98.0)), 1)
            aptitude = round(float(np.random.uniform(85.0, 96.0)), 1)
            mock_interview = round(float(np.random.uniform(85.0, 95.0)), 1)
            coding = round(float(np.random.uniform(88.0, 99.0)), 1)
            lms_completion = round(float(np.random.uniform(92.0, 100.0)), 1)

        # Edge Case 8: Insufficient Data record (almost all metrics missing) (index 90)
        elif i == 90:
            cgpa = np.nan
            backlogs = np.nan
            internal_pct = np.nan
            attendance = np.nan
            lab_attendance = np.nan
            lms_completion = np.nan
            lms_video = np.nan
            aptitude = np.nan
            mock_interview = np.nan
            coding = np.nan
            tech_mcq = np.nan
            mentor_rating = np.nan

        record = {
            "student_id": s_id,
            "name": name,
            "department": dept,
            "semester": sem,
            "gender": gender,
            "cgpa": cgpa,
            "backlogs": backlogs,
            "internal_test_pct": internal_pct,
            "attendance_pct": attendance,
            "lab_attendance_pct": lab_attendance,
            "lms_assignment_completion_pct": lms_completion,
            "lms_video_watch_pct": lms_video,
            "lms_login_frequency_per_week": lms_logins,
            "aptitude_score": aptitude,
            "mock_interview_score": mock_interview,
            "placement_registered": placement_reg,
            "coding_score": coding,
            "technical_mcq_score": tech_mcq,
            "certifications_count": certs,
            "mentor_rating": mentor_rating,
            "club_participation_score": club_participation,
            "feedback_sentiment_pct": sentiment_pct,
        }
        records.append(record)

    df = pd.DataFrame(records)
    return df


def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    """Validate DataFrame against the feature schema.
    
    Checks:
    - Missing required identifier columns
    - Duplicate student IDs
    - Out-of-bounds numeric values
    - Missing-value summaries
    - Row-level completeness assessment
    """
    report: Dict[str, Any] = {
        "is_valid": True,
        "total_rows": len(df),
        "total_cols": len(df.columns),
        "errors": [],
        "warnings": [],
        "missing_summary": {},
        "duplicate_ids": [],
        "range_violations": [],
        "completeness_avg": 0.0,
    }

    if df.empty:
        report["is_valid"] = False
        report["errors"].append("Uploaded dataset is empty.")
        return False, report

    # 1. Required identifier check
    if "student_id" not in df.columns:
        report["is_valid"] = False
        report["errors"].append("Critical column 'student_id' is missing from the dataset.")
        return False, report

    # 2. Duplicate student ID check
    dup_ids = df[df["student_id"].duplicated(keep=False)]["student_id"].unique().tolist()
    if dup_ids:
        report["duplicate_ids"] = [str(x) for x in dup_ids]
        report["warnings"].append(
            f"Found {len(dup_ids)} duplicate student ID(s): {dup_ids[:5]}"
            + ("..." if len(dup_ids) > 5 else "")
        )

    # 3. Missing values summary
    missing = df.isnull().sum()
    report["missing_summary"] = {
        col: int(cnt) for col, cnt in missing.items() if cnt > 0
    }

    # 4. Numeric Range Validation
    for col, spec in FEATURE_SCHEMA.items():
        if col in df.columns and ("min" in spec or "max" in spec):
            col_series = pd.to_numeric(df[col], errors="coerce")
            min_val = spec.get("min")
            max_val = spec.get("max")

            if min_val is not None:
                below = df[col_series < min_val]
                if not below.empty:
                    msg = f"Column '{col}' has {len(below)} values below minimum allowed {min_val}."
                    report["range_violations"].append(msg)
                    report["warnings"].append(msg)

            if max_val is not None:
                above = df[col_series > max_val]
                if not above.empty:
                    msg = f"Column '{col}' has {len(above)} values exceeding maximum allowed {max_val}."
                    report["range_violations"].append(msg)
                    report["warnings"].append(msg)

    # 5. Row-level indicator completeness
    indicator_cols = [
        "cgpa", "internal_test_pct", "attendance_pct",
        "lms_assignment_completion_pct", "aptitude_score",
        "mock_interview_score", "coding_score", "mentor_rating"
    ]
    present_indicators = [c for c in indicator_cols if c in df.columns]
    if present_indicators:
        non_null_counts = df[present_indicators].notnull().sum(axis=1)
        completeness_pcts = (non_null_counts / len(present_indicators)) * 100.0
        report["completeness_avg"] = round(float(completeness_pcts.mean()), 1)
    else:
        report["completeness_avg"] = 0.0

    return report["is_valid"], report


def merge_student_datasets(datasets: Dict[str, pd.DataFrame]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Merge multiple separate domain CSV tables on 'student_id'.
    
    Prevents double counting or silent drops by using outer join on student_id,
    with an audit summary.
    """
    audit: Dict[str, Any] = {
        "source_tables": list(datasets.keys()),
        "table_row_counts": {k: len(v) for k, v in datasets.items()},
        "merged_rows": 0,
        "warnings": [],
    }

    if not datasets:
        return pd.DataFrame(), audit

    # Start with student demographics table if present, otherwise first available
    primary_key = "student_id"
    tables = list(datasets.items())

    merged_df = None
    for name, df in tables:
        if primary_key not in df.columns:
            audit["warnings"].append(f"Table '{name}' lacks '{primary_key}' and was skipped.")
            continue

        clean_df = df.copy()
        # Drop duplicates within table on student_id
        if clean_df[primary_key].duplicated().any():
            audit["warnings"].append(f"Table '{name}' had duplicate IDs; keeping first occurrence.")
            clean_df = clean_df.drop_duplicates(subset=[primary_key], keep="first")

        if merged_df is None:
            merged_df = clean_df
        else:
            # Suffix overlapping non-key columns if any
            overlap = [c for c in clean_df.columns if c in merged_df.columns and c != primary_key]
            if overlap:
                for col in overlap:
                    # Keep existing non-null or combine
                    clean_df = clean_df.rename(columns={col: f"{col}_{name}"})

            merged_df = pd.merge(merged_df, clean_df, on=primary_key, how="outer")

    if merged_df is not None:
        audit["merged_rows"] = len(merged_df)
    else:
        merged_df = pd.DataFrame()

    return merged_df, audit


def save_sample_templates(output_dir: str = "data/templates") -> Dict[str, str]:
    """Generate and save downloadable sample CSV templates and synthetic dataset."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_dir) or "data", exist_ok=True)

    # 1. Full Unified Template
    unified_df = generate_synthetic_dataset(num_students=100, seed=42)
    unified_path = os.path.join(output_dir, "unified_student_dataset_template.csv")
    unified_df.to_csv(unified_path, index=False)

    # Also save as main demonstration dataset
    main_demo_path = os.path.join(os.path.dirname(output_dir), "synthetic_students.csv")
    unified_df.to_csv(main_demo_path, index=False)

    # 2. Demographics Template
    demo_cols = ["student_id", "name", "department", "semester", "gender"]
    demo_path = os.path.join(output_dir, "1_student_demographics_template.csv")
    unified_df[demo_cols].head(10).to_csv(demo_path, index=False)

    # 3. Academics Template
    acad_cols = ["student_id", "cgpa", "backlogs", "internal_test_pct"]
    acad_path = os.path.join(output_dir, "2_academics_template.csv")
    unified_df[acad_cols].head(10).to_csv(acad_path, index=False)

    # 4. Attendance Template
    att_cols = ["student_id", "attendance_pct", "lab_attendance_pct"]
    att_path = os.path.join(output_dir, "3_attendance_template.csv")
    unified_df[att_cols].head(10).to_csv(att_path, index=False)

    # 5. LMS Template
    lms_cols = [
        "student_id",
        "lms_assignment_completion_pct",
        "lms_video_watch_pct",
        "lms_login_frequency_per_week",
    ]
    lms_path = os.path.join(output_dir, "4_lms_activity_template.csv")
    unified_df[lms_cols].head(10).to_csv(lms_path, index=False)

    # 6. Placement Template
    place_cols = ["student_id", "aptitude_score", "mock_interview_score", "placement_registered"]
    place_path = os.path.join(output_dir, "5_placement_readiness_template.csv")
    unified_df[place_cols].head(10).to_csv(place_path, index=False)

    # 7. Skills Assessment Template
    skills_cols = ["student_id", "coding_score", "technical_mcq_score", "certifications_count"]
    skills_path = os.path.join(output_dir, "6_skills_assessment_template.csv")
    unified_df[skills_cols].head(10).to_csv(skills_path, index=False)

    # 8. Engagement & Feedback Template
    eng_cols = ["student_id", "mentor_rating", "club_participation_score", "feedback_sentiment_pct"]
    eng_path = os.path.join(output_dir, "7_engagement_feedback_template.csv")
    unified_df[eng_cols].head(10).to_csv(eng_path, index=False)

    return {
        "unified": unified_path,
        "demographics": demo_path,
        "academics": acad_path,
        "attendance": att_path,
        "lms": lms_path,
        "placement": place_path,
        "skills": skills_path,
        "engagement": eng_path,
        "demo_data": main_demo_path,
    }
