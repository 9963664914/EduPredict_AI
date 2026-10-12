"""Interactive Plotly visualizations styled for a dark navy hackathon dashboard.

EduPredict AI - byteXL HacXLerate 2026 (Problem Statement 4 by KPMG in India)
"""

from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# Theme Palette
THEME = {
    "bg": "#0f172a",          # Slate 900
    "card_bg": "#1e293b",     # Slate 800
    "text": "#f8fafc",        # Slate 50
    "muted_text": "#94a3b8",  # Slate 400
    "grid": "#334155",        # Slate 700
    "blue": "#3b82f6",
    "cyan": "#06b6d4",
    "purple": "#8b5cf6",
    "green": "#10b981",
    "amber": "#f59e0b",
    "red": "#ef4444",
}


def apply_dark_theme(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply consistent premium dark styling to any Plotly figure."""
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>",
            "font": {"size": 16, "color": THEME["text"], "family": "Inter, sans-serif"},
            "x": 0.02,
            "xanchor": "left",
        },
        paper_bgcolor=THEME["card_bg"],
        plot_bgcolor=THEME["card_bg"],
        font={"color": THEME["text"], "family": "Inter, sans-serif"},
        margin=dict(l=40, r=30, t=50, b=40),
        legend=dict(
            font={"color": THEME["muted_text"]},
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        xaxis=dict(
            gridcolor=THEME["grid"],
            zerolinecolor=THEME["grid"],
            tickfont=dict(color=THEME["muted_text"]),
        ),
        yaxis=dict(
            gridcolor=THEME["grid"],
            zerolinecolor=THEME["grid"],
            tickfont=dict(color=THEME["muted_text"]),
        ),
        hoverlabel=dict(
            bgcolor="#0b132b",
            font_size=12,
            font_family="Inter, sans-serif",
            font_color="#ffffff",
        ),
    )
    return fig


def plot_score_distribution(df: pd.DataFrame) -> go.Figure:
    """Create a polished distribution histogram of Student Success Scores."""
    valid_scores = df["success_score"].dropna()

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=valid_scores,
        nbinsx=20,
        marker=dict(
            color=THEME["cyan"],
            line=dict(color="#ffffff", width=0.5),
            opacity=0.85,
        ),
        name="Student Count",
        hovertemplate="Score Range: %{x}<br>Count: %{y}<extra></extra>",
    ))

    # Mean line
    if not valid_scores.empty:
        mean_val = float(valid_scores.mean())
        fig.add_vline(
            x=mean_val,
            line_dash="dash",
            line_color=THEME["amber"],
            annotation_text=f"Mean: {mean_val:.1f}",
            annotation_position="top right",
            annotation_font_color=THEME["amber"],
        )

    apply_dark_theme(fig, "Student Success Score Distribution")
    fig.update_xaxes(title_text="Student Success Score (0 - 100)")
    fig.update_yaxes(title_text="Number of Students")
    return fig


def plot_academic_vs_placement(df: pd.DataFrame) -> go.Figure:
    """Quadrant scatter plot comparing Academic Performance vs Placement Readiness."""
    sub = df.dropna(subset=["pillar_academic", "pillar_placement"]).copy()

    fig = px.scatter(
        sub,
        x="pillar_academic",
        y="pillar_placement",
        color="overall_support_flag" if "overall_support_flag" in sub.columns else None,
        hover_data=["student_id", "name", "department", "cgpa", "attendance_pct"],
        color_discrete_map={
            "On Track": THEME["green"],
            "Review Recommended": THEME["amber"],
            "Academic Support Priority": "#f97316",
            "Placement Support Priority": THEME["purple"],
            "Dual Support Needed": THEME["red"],
            "Insufficient Data": "#64748b",
        },
        labels={
            "pillar_academic": "Academic Performance Pillar (0-100)",
            "pillar_placement": "Placement Readiness Pillar (0-100)",
            "overall_support_flag": "Support Status",
        },
    )

    # Quadrant benchmark lines (Benchmark 60)
    fig.add_hline(y=60.0, line_dash="dot", line_color=THEME["grid"], annotation_text="Placement Cutoff (60)")
    fig.add_vline(x=60.0, line_dash="dot", line_color=THEME["grid"], annotation_text="Academic Cutoff (60)")

    fig.update_traces(marker=dict(size=9, opacity=0.85, line=dict(width=1, color="#ffffff")))
    apply_dark_theme(fig, "Academic vs. Placement Readiness Quadrant")
    return fig


def plot_department_comparison(df: pd.DataFrame) -> go.Figure:
    """Bar chart comparing average Success Score and risk count across departments."""
    if "department" not in df.columns:
        return go.Figure()

    dept_stats = df.groupby("department").agg(
        avg_score=("success_score", "mean"),
        total_students=("student_id", "count"),
        acad_support=("academic_risk_status", lambda s: (s == "Support recommended").sum()),
        place_support=("placement_risk_status", lambda s: (s == "Support recommended").sum()),
    ).reset_index()

    dept_stats["avg_score"] = dept_stats["avg_score"].round(1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dept_stats["department"],
        y=dept_stats["avg_score"],
        name="Avg Success Score",
        marker_color=THEME["blue"],
        text=dept_stats["avg_score"],
        textposition="auto",
        hovertemplate="Dept: %{x}<br>Avg Score: %{y:.1f}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=dept_stats["department"],
        y=dept_stats["acad_support"],
        name="Academic Support Needed",
        marker_color=THEME["red"],
        text=dept_stats["acad_support"],
        textposition="auto",
        hovertemplate="Dept: %{x}<br>Need Academic Support: %{y}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=dept_stats["department"],
        y=dept_stats["place_support"],
        name="Placement Support Needed",
        marker_color=THEME["purple"],
        text=dept_stats["place_support"],
        textposition="auto",
        hovertemplate="Dept: %{x}<br>Need Placement Support: %{y}<extra></extra>",
    ))

    apply_dark_theme(fig, "Department Performance & Support Demand")
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text="Department")
    fig.update_yaxes(title_text="Metric Value")
    return fig


def plot_segment_donut(df: pd.DataFrame) -> go.Figure:
    """Donut chart showing student segmentation proportion."""
    if "student_segment" not in df.columns:
        return go.Figure()

    counts = df["student_segment"].value_counts().reset_index()
    counts.columns = ["segment", "count"]

    color_map = {
        "Insufficient data": "#94a3b8",
        "Multiple support needs": "#ef4444",
        "Low attendance, reasonable academics": "#f59e0b",
        "Low academics, adequate attendance": "#f97316",
        "Strong academics, low placement readiness": "#8b5cf6",
        "Strong performance across available indicators": "#10b981",
        "Moderate / Consistent progress": "#06b6d4",
    }
    colors = [color_map.get(s, "#3b82f6") for s in counts["segment"]]

    fig = go.Figure(data=[go.Pie(
        labels=counts["segment"],
        values=counts["count"],
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#0f172a", width=2)),
        textinfo="label+percent",
        hovertemplate="Segment: %{label}<br>Count: %{value} (%{percent})<extra></extra>",
    )])

    apply_dark_theme(fig, "Student Cohort Segmentation")
    fig.update_layout(showlegend=False)
    return fig


def plot_student_radar(pillars: Dict[str, Optional[float]], student_name: str = "") -> go.Figure:
    """Spider / Radar chart displaying the 6 pillar performance for a single student."""
    categories = [
        "Academic Performance",
        "Attendance",
        "LMS Completion",
        "Placement Readiness",
        "Skills Assessment",
        "Engagement & Feedback",
    ]
    keys = [
        "academic_performance",
        "attendance",
        "lms_completion",
        "placement_readiness",
        "skills_assessment",
        "engagement_feedback",
    ]

    values = [pillars.get(k) if pillars.get(k) is not None else 0.0 for k in keys]
    # Close the polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()

    # Benchmark target line (75)
    fig.add_trace(go.Scatterpolar(
        r=[75] * len(categories_closed),
        theta=categories_closed,
        fill=None,
        line=dict(color=THEME["muted_text"], dash="dash", width=1),
        name="Benchmark (75)",
        hoverinfo="none",
    ))

    # Student polygon
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(6, 182, 212, 0.25)",
        line=dict(color=THEME["cyan"], width=2.5),
        name=student_name or "Student Score",
        hovertemplate="Pillar: %{theta}<br>Score: %{r:.1f}/100<extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor=THEME["grid"],
                tickfont=dict(color=THEME["muted_text"], size=10),
            ),
            angularaxis=dict(
                gridcolor=THEME["grid"],
                tickfont=dict(color=THEME["text"], size=11, family="Inter, sans-serif"),
            ),
            bgcolor=THEME["card_bg"],
        ),
        paper_bgcolor=THEME["card_bg"],
        plot_bgcolor=THEME["card_bg"],
        font={"color": THEME["text"], "family": "Inter, sans-serif"},
        margin=dict(l=50, r=50, t=40, b=40),
        legend=dict(
            font={"color": THEME["muted_text"]},
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
        ),
    )
    return fig


def plot_attendance_vs_cgpa(df: pd.DataFrame) -> go.Figure:
    """Scatter plot illustrating correlation between Attendance and CGPA."""
    sub = df.dropna(subset=["attendance_pct", "cgpa"]).copy()

    fig = px.scatter(
        sub,
        x="attendance_pct",
        y="cgpa",
        color="student_segment" if "student_segment" in sub.columns else None,
        hover_data=["student_id", "name", "department"],
        trendline="ols",
        labels={"attendance_pct": "Overall Attendance (%)", "cgpa": "CGPA (0 - 10.0)"},
    )

    fig.update_traces(marker=dict(size=8, opacity=0.85, line=dict(width=1, color="#ffffff")))
    apply_dark_theme(fig, "Attendance vs. Academic CGPA")
    return fig
