"""EduPredict AI - Student Analytics & Success Platform.

byteXL HacXLerate 2026 | Problem Statement 4 by KPMG in India
"""

import os
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
import streamlit as st

# Import core analytical modules
from modules.data_processing import (
    generate_synthetic_dataset,
    validate_dataframe,
    merge_student_datasets,
    save_sample_templates,
    FEATURE_SCHEMA,
)
from modules.scoring import (
    DEFAULT_WEIGHTS,
    calculate_student_score,
    compute_dataset_scores,
)
from modules.risk_analysis import (
    DEFAULT_RISK_THRESHOLDS,
    assess_student_academic_risk,
    assess_student_placement_risk,
    compute_dataset_risks,
)
from modules.segmentation import (
    SEGMENT_DEFINITIONS,
    compute_dataset_segments,
    get_segment_statistics,
)
from modules.recommendations import (
    generate_student_recommendations,
    generate_recommendations_summary,
)
from modules.visualizations import (
    plot_score_distribution,
    plot_academic_vs_placement,
    plot_department_comparison,
    plot_segment_donut,
    plot_student_radar,
    plot_attendance_vs_cgpa,
)
from modules.report_export import (
    METHODOLOGY_SUMMARY,
    export_dataframe_to_csv,
    get_academic_support_export,
    get_placement_support_export,
    get_comprehensive_export,
)


# --- Page Configuration ---
st.set_page_config(
    page_title="EduPredict AI | Student Analytics Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom Premium Dark Navy CSS Styling ---
CUSTOM_CSS = """
<style>
/* Base Dark Theme Overrides */
.stApp {
    background-color: #0a0f1d;
    color: #e2e8f0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #0f172a !important;
    border-right: 1px solid #1e293b;
}

/* Glassmorphism KPI Metric Cards */
.kpi-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 15px;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.kpi-card:hover {
    transform: translateY(-2px);
    border-color: rgba(6, 182, 212, 0.3);
}
.kpi-title {
    color: #94a3b8;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}
.kpi-value {
    color: #f8fafc;
    font-size: 2.1rem;
    font-weight: 700;
    line-height: 1.2;
}
.kpi-subtext {
    color: #64748b;
    font-size: 0.8rem;
    margin-top: 6px;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}
.badge-green { background-color: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
.badge-amber { background-color: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
.badge-red { background-color: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
.badge-purple { background-color: rgba(139, 92, 246, 0.15); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.3); }
.badge-cyan { background-color: rgba(6, 182, 212, 0.15); color: #22d3ee; border: 1px solid rgba(6, 182, 212, 0.3); }
.badge-slate { background-color: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); }

/* Notice Banner */
.notice-box {
    background-color: rgba(30, 41, 59, 0.8);
    border-left: 4px solid #3b82f6;
    border-radius: 6px;
    padding: 12px 18px;
    margin-bottom: 20px;
    font-size: 0.88rem;
    color: #cbd5e1;
}

/* Tab & Header adjustments */
h1, h2, h3, h4 {
    color: #f8fafc !important;
    font-weight: 700 !important;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #1e293b;
    border-radius: 8px;
    overflow: hidden;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# --- User Accounts & Authentication Config ---
USER_ACCOUNTS = {
    "admin": {
        "password": "admin@2026",
        "name": "Dr. K. S. Sharma",
        "role": "Dean / Administrator",
        "avatar": "👑",
        "badge": "badge-purple",
    },
    "advisor": {
        "password": "advisor@2026",
        "name": "Prof. Sneha Verma",
        "role": "Academic Advisor",
        "avatar": "📚",
        "badge": "badge-cyan",
    },
    "tpo": {
        "password": "tpo@2026",
        "name": "Mr. Arjun Reddy",
        "role": "Placement Officer (TPO)",
        "avatar": "💼",
        "badge": "badge-green",
    },
    "hod": {
        "password": "hod@2026",
        "name": "Dr. Meera Iyer",
        "role": "Department Head (HOD)",
        "avatar": "🏛️",
        "badge": "badge-amber",
    },
}

# --- Session State Initialization ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "user_info" not in st.session_state:
    st.session_state["user_info"] = None

@st.cache_data
def load_default_data() -> pd.DataFrame:
    """Generate and return default synthetic demonstration data."""
    save_sample_templates("data/templates")
    return generate_synthetic_dataset(num_students=100, seed=42)

if "raw_data" not in st.session_state:
    st.session_state["raw_data"] = load_default_data()

if "weights" not in st.session_state:
    st.session_state["weights"] = DEFAULT_WEIGHTS.copy()

if "thresholds" not in st.session_state:
    st.session_state["thresholds"] = DEFAULT_RISK_THRESHOLDS.copy()


def render_login_screen():
    """Render a modern dark-navy glassmorphic login screen for institutional authentication."""
    st.write("")
    st.write("")
    col_left, col_mid, col_right = st.columns([1, 1.4, 1])

    with col_mid:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 25px;">
                <div style="width: 58px; height: 58px; background: linear-gradient(135deg, #3b82f6, #06b6d4); border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; font-size: 30px; box-shadow: 0 4px 15px rgba(6,182,212,0.4); margin-bottom: 12px;">🎓</div>
                <h2 style="margin: 0; color: #f8fafc; font-size: 1.85rem; font-weight: 800;">EduPredict AI</h2>
                <p style="margin: 4px 0 0 0; color: #06b6d4; font-size: 0.9rem; font-weight: 600;">Smarter Insights. Transparent Evaluation. Actionable Support.</p>
                <p style="margin: 2px 0 0 0; color: #64748b; font-size: 0.78rem;">byteXL HacXLerate 2026 | Problem Statement 4 by KPMG in India</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            st.markdown("<p style='font-size:0.92rem; font-weight:700; color:#e2e8f0; margin-bottom:12px;'>🔐 Institutional Sign In</p>", unsafe_allow_html=True)
            u_input = st.text_input("Username", placeholder="e.g. admin, advisor, tpo, hod")
            p_input = st.text_input("Password", type="password", placeholder="Enter account password")
            submit_login = st.form_submit_button("Sign In to Platform", use_container_width=True)

            if submit_login:
                clean_u = u_input.strip().lower()
                if clean_u in USER_ACCOUNTS and USER_ACCOUNTS[clean_u]["password"] == p_input:
                    st.session_state["authenticated"] = True
                    st.session_state["user_info"] = USER_ACCOUNTS[clean_u]
                    st.session_state["username"] = clean_u
                    st.success(f"Welcome back, {USER_ACCOUNTS[clean_u]['name']}! Loading workspace...")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Check demo credentials below.")

        st.markdown("<p style='font-size:0.75rem; font-weight:700; color:#94a3b8; text-transform:uppercase; margin-top:22px; text-align:center;'>⚡ Quick Demo Access for Hackathon Judges</p>", unsafe_allow_html=True)
        q1, q2 = st.columns(2)
        with q1:
            if st.button("👑 Dean / Admin", use_container_width=True):
                st.session_state["authenticated"] = True
                st.session_state["user_info"] = USER_ACCOUNTS["admin"]
                st.session_state["username"] = "admin"
                st.rerun()
            if st.button("💼 Placement Officer", use_container_width=True):
                st.session_state["authenticated"] = True
                st.session_state["user_info"] = USER_ACCOUNTS["tpo"]
                st.session_state["username"] = "tpo"
                st.rerun()
        with q2:
            if st.button("📚 Academic Advisor", use_container_width=True):
                st.session_state["authenticated"] = True
                st.session_state["user_info"] = USER_ACCOUNTS["advisor"]
                st.session_state["username"] = "advisor"
                st.rerun()
            if st.button("🏛️ Dept Head (HOD)", use_container_width=True):
                st.session_state["authenticated"] = True
                st.session_state["user_info"] = USER_ACCOUNTS["hod"]
                st.session_state["username"] = "hod"
                st.rerun()

        with st.expander("🔑 View Demo Account Credentials Reference"):
            st.markdown("""
                | Role | Username | Password |
                | :--- | :--- | :--- |
                | **Dean / Administrator** | `admin` | `admin@2026` |
                | **Academic Advisor** | `advisor` | `advisor@2026` |
                | **Placement Officer (TPO)** | `tpo` | `tpo@2026` |
                | **Department Head (HOD)** | `hod` | `hod@2026` |
            """)


# Authentication Check Barrier
if not st.session_state.get("authenticated", False):
    render_login_screen()
    st.stop()


def get_processed_dataset() -> pd.DataFrame:
    """Run scoring, risk assessment, and segmentation pipeline on active dataset."""
    df = st.session_state["raw_data"].copy()
    w = st.session_state["weights"]
    th = st.session_state["thresholds"]

    # 1. Scoring
    scored_df = compute_dataset_scores(df, w)
    # 2. Risk analysis
    risked_df = compute_dataset_risks(scored_df, th)
    # 3. Segmentation
    segmented_df = compute_dataset_segments(risked_df)
    return segmented_df


# --- Sidebar Navigation & Global Controls ---
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
            <div style="background: linear-gradient(135deg, #3b82f6, #06b6d4); width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px;">🎓</div>
            <div>
                <h3 style="margin: 0; font-size: 1.25rem; font-weight: 800; color: #f8fafc;">EduPredict AI</h3>
                <span style="font-size: 0.72rem; color: #94a3b8;">byteXL HacXLerate 2026 | KPMG</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Active User Profile Badge
    u_info = st.session_state.get("user_info", {})
    if u_info:
        st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 8px; padding: 10px 12px; margin-bottom: 15px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.3rem;">{u_info.get('avatar', '👤')}</span>
                    <div>
                        <div style="font-size: 0.85rem; font-weight: 700; color: #f8fafc;">{u_info.get('name', 'User')}</div>
                        <span class="badge {u_info.get('badge', 'badge-cyan')}">{u_info.get('role', 'Faculty')}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    nav_option = st.radio(
        "Navigation",
        [
            "📊 Executive Dashboard",
            "🔍 Student Explorer",
            "🏷️ Cohort Segmentation",
            "💡 Intervention Center",
            "📂 Data Integration & Upload",
            "⚙️ Configurable Weights",
            "📑 Reports & Methodology",
        ],
        index=0,
        label_visibility="collapsed",
    )

    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["user_info"] = None
        st.session_state["username"] = None
        st.rerun()

    st.markdown("---")
    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#94a3b8;'>GLOBAL COHORT FILTERS</p>", unsafe_allow_html=True)

    full_df = get_processed_dataset()

    # Department filter
    all_depts = sorted(full_df["department"].dropna().unique().tolist()) if "department" in full_df.columns else []
    selected_depts = st.multiselect("Department", all_depts, default=[])

    # Semester filter
    all_sems = sorted(full_df["semester"].dropna().unique().tolist()) if "semester" in full_df.columns else []
    selected_sems = st.multiselect("Semester", all_sems, default=[])

    # Academic Risk filter
    acad_risks = ["On track", "Needs review", "Support recommended", "Insufficient data"]
    selected_acad_risk = st.multiselect("Academic Support Flag", acad_risks, default=[])

    # Placement Risk filter
    place_risks = ["On track", "Needs review", "Support recommended", "Insufficient data"]
    selected_place_risk = st.multiselect("Placement Support Flag", place_risks, default=[])

    # Segment filter
    all_segments = list(SEGMENT_DEFINITIONS.keys())
    selected_segments = st.multiselect("Student Segment", all_segments, default=[])

    # Search by ID or Name
    search_query = st.text_input("Search ID or Name", placeholder="e.g. STU0014 or Sharma")

    st.markdown("---")
    st.markdown("""
        <div style="font-size: 0.73rem; color: #64748b; line-height: 1.4;">
            <b>Advisory Disclaimer:</b><br>
            Student Success Scores are transparent prototype indicators. Human review is required for all academic actions.
        </div>
    """, unsafe_allow_html=True)


# --- Apply Active Filters to Dataset ---
filtered_df = full_df.copy()

if selected_depts:
    filtered_df = filtered_df[filtered_df["department"].isin(selected_depts)]
if selected_sems:
    filtered_df = filtered_df[filtered_df["semester"].isin(selected_sems)]
if selected_acad_risk:
    filtered_df = filtered_df[filtered_df["academic_risk_status"].isin(selected_acad_risk)]
if selected_place_risk:
    filtered_df = filtered_df[filtered_df["placement_risk_status"].isin(selected_place_risk)]
if selected_segments:
    filtered_df = filtered_df[filtered_df["student_segment"].isin(selected_segments)]
if search_query:
    q = search_query.strip().lower()
    filtered_df = filtered_df[
        filtered_df["student_id"].str.lower().str.contains(q, na=False) |
        filtered_df["name"].str.lower().str.contains(q, na=False)
    ]


# ==============================================================================
# TAB 1: EXECUTIVE DASHBOARD
# ==============================================================================
if nav_option == "📊 Executive Dashboard":
    st.markdown("## 📊 Executive Student Success Dashboard")
    st.markdown(
        "<p style='color:#94a3b8; margin-top:-10px;'>"
        "Real-time institutional analytics across Academic, Attendance, LMS, Skills, and Placement dimensions."
        "</p>",
        unsafe_allow_html=True,
    )

    # Empty State Check
    if filtered_df.empty:
        st.warning("No student records match the active filter criteria. Adjust your sidebar filters.")
    else:
        # Top KPI Metric Cards
        total_count = len(filtered_df)
        valid_scores = filtered_df["success_score"].dropna()
        avg_score = round(float(valid_scores.mean()), 1) if not valid_scores.empty else "N/A"
        
        acad_need = (filtered_df["academic_risk_status"] == "Support recommended").sum()
        place_need = (filtered_df["placement_risk_status"] == "Support recommended").sum()
        avg_att = round(float(filtered_df["attendance_pct"].dropna().mean()), 1) if not filtered_df["attendance_pct"].dropna().empty else "N/A"
        avg_cgpa = round(float(filtered_df["cgpa"].dropna().mean()), 2) if not filtered_df["cgpa"].dropna().empty else "N/A"

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Total Cohort</div>
                    <div class="kpi-value">{total_count}</div>
                    <div class="kpi-subtext">Active student records</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Avg Success Score</div>
                    <div class="kpi-value" style="color:#06b6d4;">{avg_score}</div>
                    <div class="kpi-subtext">0 - 100 normalized index</div>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Academic Support</div>
                    <div class="kpi-value" style="color:#ef4444;">{acad_need}</div>
                    <div class="kpi-subtext">{round((acad_need/total_count)*100, 1)}% of filtered cohort</div>
                </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Placement Support</div>
                    <div class="kpi-value" style="color:#8b5cf6;">{place_need}</div>
                    <div class="kpi-subtext">{round((place_need/total_count)*100, 1)}% of filtered cohort</div>
                </div>
            """, unsafe_allow_html=True)
        with c5:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Avg Attendance & CGPA</div>
                    <div class="kpi-value" style="color:#10b981; font-size:1.6rem;">{avg_att}% / {avg_cgpa}</div>
                    <div class="kpi-subtext">Overall institutional health</div>
                </div>
            """, unsafe_allow_html=True)

        # Automated Diagnostic Insight Banner
        dual_need = (filtered_df["overall_support_flag"] == "Dual Support Needed").sum()
        strong_students = (filtered_df["student_segment"] == "Strong performance across available indicators").sum()
        acad_place_gap = (filtered_df["student_segment"] == "Strong academics, low placement readiness").sum()

        st.markdown(f"""
            <div class="notice-box">
                <b>💡 Automated Diagnostic Insights:</b>
                <ul style="margin: 6px 0 0 18px; padding: 0;">
                    <li><b>{dual_need} student(s)</b> require concurrent academic & placement intervention (Dual Support Priority).</li>
                    <li><b>{acad_place_gap} student(s)</b> demonstrate strong academic performance but lag significantly in placement readiness, suggesting targeted aptitude & coding bootcamps will yield highest ROI.</li>
                    <li><b>{strong_students} student(s)</b> excel across all 6 performance pillars and are ready for peer-tutoring and dream placement fast-tracks.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

        # Charts Row 1: Score Distribution & Quadrant Analysis
        r1_c1, r1_c2 = st.columns([1, 1])
        with r1_c1:
            fig_dist = plot_score_distribution(filtered_df)
            st.plotly_chart(fig_dist, use_container_width=True)
        with r1_c2:
            fig_quad = plot_academic_vs_placement(filtered_df)
            st.plotly_chart(fig_quad, use_container_width=True)

        # Charts Row 2: Department Comparison & Attendance vs CGPA
        r2_c1, r2_c2 = st.columns([1.2, 1])
        with r2_c1:
            fig_dept = plot_department_comparison(filtered_df)
            st.plotly_chart(fig_dept, use_container_width=True)
        with r2_c2:
            fig_donut = plot_segment_donut(filtered_df)
            st.plotly_chart(fig_donut, use_container_width=True)


# ==============================================================================
# TAB 2: STUDENT EXPLORER
# ==============================================================================
elif nav_option == "🔍 Student Explorer":
    st.markdown("## 🔍 Individual Student Explorer & Diagnostic Profile")
    st.markdown(
        "<p style='color:#94a3b8; margin-top:-10px;'>"
        "Search, filter, and inspect detailed score breakdowns, effective weights, and explainable recommendations."
        "</p>",
        unsafe_allow_html=True,
    )

    if filtered_df.empty:
        st.warning("No student records match the current filters.")
    else:
        # Table of students
        display_cols = [
            "student_id", "name", "department", "semester", "cgpa", "backlogs",
            "attendance_pct", "success_score", "academic_risk_status",
            "placement_risk_status", "student_segment"
        ]
        available_cols = [c for c in display_cols if c in filtered_df.columns]

        st.dataframe(
            filtered_df[available_cols].style.format({
                "cgpa": "{:.2f}",
                "attendance_pct": "{:.1f}%",
                "success_score": lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A",
            }),
            use_container_width=True,
            height=280,
        )

        st.markdown("---")
        st.markdown("### 📋 Student Diagnostic Profile Inspector")

        # Select student
        student_id_options = filtered_df["student_id"].tolist()
        selected_id = st.selectbox(
            "Select a Student ID to inspect in depth:",
            student_id_options,
            format_func=lambda s: f"{s} — {filtered_df[filtered_df['student_id'] == s]['name'].values[0]} ({filtered_df[filtered_df['student_id'] == s]['department'].values[0]})"
        )

        if selected_id:
            s_row = filtered_df[filtered_df["student_id"] == selected_id].iloc[0]
            calc_details = calculate_student_score(s_row, st.session_state["weights"])
            recs = generate_student_recommendations(s_row)

            # Profile Header
            p_col1, p_col2, p_col3, p_col4 = st.columns([1.2, 1, 1, 1])
            with p_col1:
                st.markdown(f"""
                    <div style="background:#1e293b; padding:15px; border-radius:10px; border:1px solid #334155;">
                        <h3 style="margin:0; color:#f8fafc;">{s_row.get('name', 'Unknown')}</h3>
                        <p style="margin:3px 0 0 0; color:#94a3b8; font-size:0.85rem;">
                            <b>ID:</b> {s_row['student_id']} | <b>Dept:</b> {s_row.get('department', 'N/A')} | {s_row.get('semester', 'N/A')}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            with p_col2:
                score_val = calc_details["score"]
                score_str = f"{score_val:.1f}" if pd.notnull(score_val) else "Unavailable"
                st.markdown(f"""
                    <div style="background:#1e293b; padding:15px; border-radius:10px; border:1px solid #334155; text-align:center;">
                        <span style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase;">Success Score</span>
                        <h2 style="margin:2px 0 0 0; color:#06b6d4; font-size:1.8rem;">{score_str} <span style="font-size:0.9rem; color:#64748b;">/100</span></h2>
                    </div>
                """, unsafe_allow_html=True)
            with p_col3:
                comp = calc_details["completeness_pct"]
                st.markdown(f"""
                    <div style="background:#1e293b; padding:15px; border-radius:10px; border:1px solid #334155; text-align:center;">
                        <span style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase;">Data Completeness</span>
                        <h2 style="margin:2px 0 0 0; color:#10b981; font-size:1.8rem;">{comp}%</h2>
                    </div>
                """, unsafe_allow_html=True)
            with p_col4:
                seg = s_row.get("student_segment", "N/A")
                st.markdown(f"""
                    <div style="background:#1e293b; padding:15px; border-radius:10px; border:1px solid #334155; text-align:center;">
                        <span style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase;">Assigned Segment</span>
                        <p style="margin:8px 0 0 0; color:#c084fc; font-weight:700; font-size:0.85rem;">{seg}</p>
                    </div>
                """, unsafe_allow_html=True)

            st.write("")

            # Main Diagnostic Breakdown: Radar Chart & Pillar Metrics
            prof_c1, prof_c2 = st.columns([1.1, 1])
            with prof_c1:
                radar_fig = plot_student_radar(calc_details["pillars"], str(s_row.get("name", "")))
                st.plotly_chart(radar_fig, use_container_width=True)

            with prof_c2:
                st.markdown("#### ⚖️ Pillar Breakdown & Effective Weights")
                pillar_data = []
                for p_name, p_val in calc_details["pillars"].items():
                    eff_w = calc_details["effective_weights"].get(p_name, 0.0)
                    pillar_data.append({
                        "Pillar": p_name.replace("_", " ").title(),
                        "Score": f"{p_val:.1f}/100" if p_val is not None else "Missing / Not Available",
                        "Effective Weight": f"{eff_w*100:.1f}%",
                    })
                st.table(pd.DataFrame(pillar_data))

                st.markdown(f"""
                    <p style="font-size:0.85rem; color:#cbd5e1;">
                        <b>Strongest Dimension:</b> <span class="badge badge-green">{str(calc_details['strongest_pillar']).replace('_', ' ').title() if calc_details['strongest_pillar'] else 'None'}</span><br>
                        <b>Weakest Dimension:</b> <span class="badge badge-red">{str(calc_details['weakest_pillar']).replace('_', ' ').title() if calc_details['weakest_pillar'] else 'None'}</span>
                    </p>
                """, unsafe_allow_html=True)

            # Calculation Steps & Transparency
            with st.expander("🔍 View Step-by-Step Mathematical Calculation & Transparency Log"):
                st.code(calc_details["calculation_steps"], language="text")

            # Risk Support Factors
            st.markdown("#### ⚠️ Independent Support Evaluation & Trigger Factors")
            r_c1, r_c2 = st.columns(2)
            with r_c1:
                st.markdown(f"""
                    <div style="background:#1e293b; padding:15px; border-radius:8px; border:1px solid #334155; height:100%;">
                        <b style="color:#f8fafc;">Academic Support Evaluation:</b> 
                        <span class="badge {'badge-green' if s_row.get('academic_risk_status') == 'On track' else 'badge-amber' if s_row.get('academic_risk_status') == 'Needs review' else 'badge-red'}">
                            {s_row.get('academic_risk_status')}
                        </span>
                        <p style="margin-top:10px; font-size:0.82rem; color:#cbd5e1;">
                            {s_row.get('academic_risk_reasons', 'No risk reasons logged.')}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            with r_c2:
                st.markdown(f"""
                    <div style="background:#1e293b; padding:15px; border-radius:8px; border:1px solid #334155; height:100%;">
                        <b style="color:#f8fafc;">Placement Readiness Evaluation:</b> 
                        <span class="badge {'badge-green' if s_row.get('placement_risk_status') == 'On track' else 'badge-amber' if s_row.get('placement_risk_status') == 'Needs review' else 'badge-purple'}">
                            {s_row.get('placement_risk_status')}
                        </span>
                        <p style="margin-top:10px; font-size:0.82rem; color:#cbd5e1;">
                            {s_row.get('placement_risk_reasons', 'No placement reasons logged.')}
                        </p>
                    </div>
                """, unsafe_allow_html=True)

            # Explainable Recommendations
            st.markdown("#### 🎯 Explainable Action Plan & Recommended Interventions")
            for r in recs:
                p_badge = "badge-red" if r["priority"] in ["Urgent", "High"] else "badge-amber" if r["priority"] == "Medium" else "badge-cyan"
                st.markdown(f"""
                    <div style="background:#1e293b; border-left:4px solid {'#ef4444' if r['priority'] in ['Urgent','High'] else '#f59e0b' if r['priority']=='Medium' else '#06b6d4'}; padding:12px 16px; border-radius:6px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <b style="color:#f8fafc; font-size:0.95rem;">{r['title']}</b>
                            <span class="badge {p_badge}">{r['priority']} Priority</span>
                        </div>
                        <div style="margin-top:6px; font-size:0.85rem; color:#cbd5e1;">
                            <b>Trigger Reason:</b> {r['trigger_reason']}<br>
                            <b>Recommended Action:</b> {r['recommended_action']}<br>
                            <span style="color:#94a3b8;"><b>Target Outcome:</b> {r['expected_outcome']}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)


# ==============================================================================
# TAB 3: COHORT SEGMENTATION
# ==============================================================================
elif nav_option == "🏷️ Cohort Segmentation":
    st.markdown("## 🏷️ Student Cohort Segmentation")
    st.markdown(
        "<p style='color:#94a3b8; margin-top:-10px;'>"
        "Multi-dimensional grouping based on mutually distinct heuristic rules with explicit precedence."
        "</p>",
        unsafe_allow_html=True,
    )

    seg_stats = get_segment_statistics(filtered_df)

    c_left, c_right = st.columns([1.2, 1])
    with c_left:
        st.markdown("#### 📊 Segment Distribution Overview")
        st.dataframe(
            seg_stats[["segment", "count", "percentage", "average_score"]].rename(columns={
                "segment": "Segment Name",
                "count": "Students",
                "percentage": "Share (%)",
                "average_score": "Avg Success Score",
            }),
            use_container_width=True,
            hide_index=True,
        )
    with c_right:
        st.plotly_chart(plot_segment_donut(filtered_df), use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔎 Segment Drill-Down & Student Roster")

    inspect_seg = st.selectbox("Select Segment to inspect cohort:", list(SEGMENT_DEFINITIONS.keys()))

    if inspect_seg:
        meta = SEGMENT_DEFINITIONS[inspect_seg]
        st.markdown(f"""
            <div style="background:#1e293b; padding:12px 18px; border-radius:8px; border-left:4px solid {meta['color']}; margin-bottom:15px;">
                <b style="color:#f8fafc; font-size:1rem;">{inspect_seg}</b> (Precedence Priority: {meta['priority']})<br>
                <span style="color:#94a3b8; font-size:0.85rem;">{meta['description']}</span>
            </div>
        """, unsafe_allow_html=True)

        seg_students = filtered_df[filtered_df["student_segment"] == inspect_seg]
        st.markdown(f"**Found {len(seg_students)} student(s) in this segment:**")

        if not seg_students.empty:
            st.dataframe(
                seg_students[[
                    "student_id", "name", "department", "semester", "cgpa",
                    "attendance_pct", "aptitude_score", "success_score",
                    "academic_risk_status", "placement_risk_status"
                ]].style.format({
                    "cgpa": "{:.2f}",
                    "attendance_pct": "{:.1f}%",
                    "aptitude_score": lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A",
                    "success_score": lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A",
                }),
                use_container_width=True,
            )


# ==============================================================================
# TAB 4: INTERVENTION CENTER
# ==============================================================================
elif nav_option == "💡 Intervention Center":
    st.markdown("## 💡 Institutional Intervention Center")
    st.markdown(
        "<p style='color:#94a3b8; margin-top:-10px;'>"
        "Data-driven action plans to allocate faculty mentoring, remedial tutoring, and placement bootcamps."
        "</p>",
        unsafe_allow_html=True,
    )

    summary_counts = generate_recommendations_summary(filtered_df)

    i_c1, i_c2 = st.columns([1, 1])
    with i_c1:
        st.markdown("#### 📈 Highest Demand Interventions Across Cohort")
        summary_df = pd.DataFrame([
            {"Intervention Action": k, "Students Requiring Action": v, "Cohort Share (%)": round((v/len(filtered_df))*100, 1)}
            for k, v in summary_counts.items()
        ])
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    with i_c2:
        st.markdown("#### 🚨 Urgent Priority Action List")
        # Students requiring dual support or urgent attendance
        urgent_df = filtered_df[
            filtered_df["overall_support_flag"].isin(["Dual Support Needed", "Academic Support Priority"])
        ]
        st.markdown(f"**{len(urgent_df)} student(s)** flagged for urgent advisory intervention:")
        if not urgent_df.empty:
            st.dataframe(
                urgent_df[["student_id", "name", "department", "cgpa", "attendance_pct", "overall_support_flag"]],
                use_container_width=True,
                hide_index=True,
            )


# ==============================================================================
# TAB 5: DATA INTEGRATION & UPLOAD
# ==============================================================================
elif nav_option == "📂 Data Integration & Upload":
    st.markdown("## 📂 Data Integration, Upload & Schema Validation")
    st.markdown(
        "<p style='color:#94a3b8; margin-top:-10px;'>"
        "Upload unified CSV or separate domain tables with instant schema audit and validation reporting."
        "</p>",
        unsafe_allow_html=True,
    )

    upload_mode = st.radio(
        "Choose Upload Structure:",
        ["Single Unified CSV Dataset", "Multiple Domain CSV Tables (Joined by student_id)"],
        horizontal=True,
    )

    if upload_mode == "Single Unified CSV Dataset":
        uploaded_file = st.file_uploader("Upload Unified Student CSV", type=["csv"])
        if uploaded_file is not None:
            try:
                new_df = pd.read_csv(uploaded_file)
                is_valid, report = validate_dataframe(new_df)

                if is_valid:
                    st.success(f"Successfully loaded {len(new_df)} student records with {len(new_df.columns)} columns.")
                    st.session_state["raw_data"] = new_df
                    st.rerun()
                else:
                    st.error("Validation failed. Please correct the following errors:")
                    for err in report["errors"]:
                        st.write(f"❌ {err}")
            except Exception as e:
                st.error(f"Error parsing CSV: {str(e)}")

    else:
        st.markdown("Upload individual departmental CSV files:")
        up_demo = st.file_uploader("1. Student Demographics CSV", type=["csv"], key="up_demo")
        up_acad = st.file_uploader("2. Academics CSV", type=["csv"], key="up_acad")
        up_att = st.file_uploader("3. Attendance CSV", type=["csv"], key="up_att")
        up_lms = st.file_uploader("4. LMS Activity CSV", type=["csv"], key="up_lms")
        up_place = st.file_uploader("5. Placement CSV", type=["csv"], key="up_place")

        if st.button("Merge & Validate Tables"):
            tables = {}
            if up_demo: tables["demographics"] = pd.read_csv(up_demo)
            if up_acad: tables["academics"] = pd.read_csv(up_acad)
            if up_att: tables["attendance"] = pd.read_csv(up_att)
            if up_lms: tables["lms"] = pd.read_csv(up_lms)
            if up_place: tables["placement"] = pd.read_csv(up_place)

            if not tables:
                st.warning("Please upload at least one CSV file.")
            else:
                merged, audit = merge_student_datasets(tables)
                is_valid, report = validate_dataframe(merged)
                if is_valid:
                    st.success(f"Successfully merged {audit['merged_rows']} student records across {len(tables)} tables!")
                    st.session_state["raw_data"] = merged
                    st.rerun()
                else:
                    st.error("Validation failed:")
                    for err in report["errors"]:
                        st.write(f"❌ {err}")

    # Active Dataset Validation Report
    st.markdown("---")
    st.markdown("### 📋 Active Dataset Validation Audit")
    _, active_report = validate_dataframe(st.session_state["raw_data"])

    a_c1, a_c2, a_c3 = st.columns(3)
    with a_c1:
        st.metric("Total Records", active_report["total_rows"])
    with a_c2:
        st.metric("Avg Profile Completeness", f"{active_report['completeness_avg']}%")
    with a_c3:
        st.metric("Duplicate Student IDs", len(active_report["duplicate_ids"]))

    if active_report["missing_summary"]:
        with st.expander("⚠️ View Missing Value Counts by Feature"):
            st.json(active_report["missing_summary"])

    if active_report["warnings"]:
        with st.expander("⚠️ View Data Quality Warnings"):
            for w in active_report["warnings"]:
                st.write(f"• {w}")

    # Reset button
    if st.button("🔄 Reset to Default 100-Student Demonstration Dataset"):
        st.session_state["raw_data"] = load_default_data()
        st.success("Reset completed!")
        st.rerun()


# ==============================================================================
# TAB 6: CONFIGURABLE WEIGHTS & THRESHOLDS
# ==============================================================================
elif nav_option == "⚙️ Configurable Weights":
    st.markdown("## ⚙️ Configurable Scoring Weights & Decision Thresholds")
    st.markdown(
        "<p style='color:#94a3b8; margin-top:-10px;'>"
        "Customize indicator weights and risk cutoffs in real-time. Changes dynamically recalculate all scores."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown("#### 1. Indicator Pillar Weights")
    st.write("Weights are automatically normalized to sum to 100%.")

    cur_w = st.session_state["weights"]
    w_c1, w_c2 = st.columns(2)

    with w_c1:
        w_acad = st.slider("Academic Performance (%)", 0, 50, int(cur_w["academic_performance"] * 100), 5)
        w_att = st.slider("Attendance Record (%)", 0, 50, int(cur_w["attendance"] * 100), 5)
        w_lms = st.slider("LMS & Assignment Completion (%)", 0, 50, int(cur_w["lms_completion"] * 100), 5)

    with w_c2:
        w_place = st.slider("Placement Readiness (%)", 0, 50, int(cur_w["placement_readiness"] * 100), 5)
        w_skills = st.slider("Technical Skills Assessment (%)", 0, 50, int(cur_w["skills_assessment"] * 100), 5)
        w_eng = st.slider("Engagement & Feedback (%)", 0, 50, int(cur_w["engagement_feedback"] * 100), 5)

    raw_sum = w_acad + w_att + w_lms + w_place + w_skills + w_eng
    if raw_sum > 0:
        new_weights = {
            "academic_performance": w_acad / raw_sum,
            "attendance": w_att / raw_sum,
            "lms_completion": w_lms / raw_sum,
            "placement_readiness": w_place / raw_sum,
            "skills_assessment": w_skills / raw_sum,
            "engagement_feedback": w_eng / raw_sum,
        }
    else:
        new_weights = DEFAULT_WEIGHTS.copy()

    if st.button("Apply New Scoring Weights"):
        st.session_state["weights"] = new_weights
        st.success("New weights applied successfully! All scores recalculated.")
        st.rerun()

    if st.button("Reset to Default Weights"):
        st.session_state["weights"] = DEFAULT_WEIGHTS.copy()
        st.success("Default weights restored.")
        st.rerun()


# ==============================================================================
# TAB 7: REPORTS & METHODOLOGY
# ==============================================================================
elif nav_option == "📑 Reports & Methodology":
    st.markdown("## 📑 Reports, Exports & Methodology Documentation")
    st.markdown(
        "<p style='color:#94a3b8; margin-top:-10px;'>"
        "Download audit-ready CSV reports and review the scoring methodology, assumptions, and ethical standards."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown("#### 📥 Instant CSV Downloads")
    d_c1, d_c2, d_c3, d_c4 = st.columns(4)

    # 1. Comprehensive Scored Dataset
    with d_c1:
        comp_df = get_comprehensive_export(filtered_df)
        st.download_button(
            "📊 Export Scored Cohort CSV",
            data=export_dataframe_to_csv(comp_df),
            file_name="edupredict_scored_cohort.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # 2. Academic Support List
    with d_c2:
        acad_df = get_academic_support_export(filtered_df)
        st.download_button(
            "📚 Export Academic Support List",
            data=export_dataframe_to_csv(acad_df),
            file_name="academic_support_roster.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # 3. Placement Support List
    with d_c3:
        place_df = get_placement_support_export(filtered_df)
        st.download_button(
            "💼 Export Placement Support List",
            data=export_dataframe_to_csv(place_df),
            file_name="placement_support_roster.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # 4. Raw Filtered Data
    with d_c4:
        st.download_button(
            "📄 Export Raw Filtered CSV",
            data=export_dataframe_to_csv(filtered_df),
            file_name="edupredict_filtered_raw.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("### 📖 Formal Methodology & Ethical Guidelines")
    st.markdown(METHODOLOGY_SUMMARY)
