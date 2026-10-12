"""Unit tests for data processing, validation, and merge operations."""

import numpy as np
import pandas as pd
import pytest
from modules.data_processing import (
    generate_synthetic_dataset,
    validate_dataframe,
    merge_student_datasets,
    FEATURE_SCHEMA,
)


def test_synthetic_data_generation():
    df = generate_synthetic_dataset(num_students=100, seed=42)
    assert len(df) == 100
    assert "student_id" in df.columns
    assert "cgpa" in df.columns
    assert "attendance_pct" in df.columns
    # Check that student IDs are unique
    assert df["student_id"].nunique() == 100


def test_validation_empty_dataframe():
    is_valid, report = validate_dataframe(pd.DataFrame())
    assert not is_valid
    assert len(report["errors"]) > 0


def test_validation_missing_student_id():
    df = pd.DataFrame({"name": ["Alice", "Bob"], "cgpa": [8.5, 7.2]})
    is_valid, report = validate_dataframe(df)
    assert not is_valid
    assert any("student_id" in e for e in report["errors"])


def test_validation_duplicate_ids():
    df = pd.DataFrame({
        "student_id": ["STU001", "STU001", "STU002"],
        "name": ["Alice", "Alice Dup", "Bob"],
        "cgpa": [8.5, 8.5, 7.2],
    })
    is_valid, report = validate_dataframe(df)
    assert is_valid  # Still valid format, but reports duplicate warnings
    assert "STU001" in report["duplicate_ids"]
    assert len(report["warnings"]) > 0


def test_validation_range_violations():
    df = pd.DataFrame({
        "student_id": ["STU001", "STU002"],
        "name": ["Alice", "Bob"],
        "cgpa": [11.5, -2.0],  # Out of bounds [0, 10]
        "attendance_pct": [120.0, 50.0],  # Out of bounds [0, 100]
    })
    is_valid, report = validate_dataframe(df)
    assert len(report["range_violations"]) > 0


def test_merge_student_datasets():
    t1 = pd.DataFrame({
        "student_id": ["S1", "S2"],
        "name": ["Alice", "Bob"],
    })
    t2 = pd.DataFrame({
        "student_id": ["S1", "S2", "S3"],
        "cgpa": [8.5, 7.0, 9.1],
    })
    t3 = pd.DataFrame({
        "student_id": ["S1", "S2"],
        "attendance_pct": [85.0, 60.0],
    })

    merged, audit = merge_student_datasets({"demo": t1, "acad": t2, "att": t3})
    assert len(merged) == 3
    assert "cgpa" in merged.columns
    assert "attendance_pct" in merged.columns
    # Check that S3 row exists with NaN for missing tables
    s3_row = merged[merged["student_id"] == "S3"].iloc[0]
    assert np.isnan(s3_row["attendance_pct"])
