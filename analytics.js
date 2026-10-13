const PILLARS = {
  academic_performance: "Academic Performance",
  attendance: "Attendance",
  lms_completion: "LMS Completion",
  placement_readiness: "Placement Readiness",
  skills_assessment: "Skills Assessment",
  engagement_feedback: "Engagement Feedback",
};

const DEFAULT_WEIGHTS = {
  academic_performance: 0.25,
  attendance: 0.2,
  lms_completion: 0.15,
  placement_readiness: 0.2,
  skills_assessment: 0.1,
  engagement_feedback: 0.1,
};

const DEFAULT_THRESHOLDS = {
  academic_cgpa_critical: 6,
  academic_cgpa_warning: 7,
  academic_attendance_critical: 65,
  academic_attendance_warning: 75,
  academic_backlogs_critical: 2,
  academic_score_critical: 55,
  academic_score_warning: 65,
  placement_aptitude_critical: 50,
  placement_aptitude_warning: 65,
  placement_interview_critical: 50,
  placement_interview_warning: 65,
  placement_coding_critical: 45,
  placement_coding_warning: 60,
  placement_score_critical: 50,
  placement_score_warning: 65,
};

const SCHEMA = {
  cgpa: [0, 10], backlogs: [0, 20], internal_test_pct: [0, 100],
  attendance_pct: [0, 100], lab_attendance_pct: [0, 100],
  lms_assignment_completion_pct: [0, 100], lms_video_watch_pct: [0, 100],
  lms_login_frequency_per_week: [0, 30], aptitude_score: [0, 100],
  mock_interview_score: [0, 100], coding_score: [0, 100],
  technical_mcq_score: [0, 100], certifications_count: [0, 15],
  mentor_rating: [1, 5], club_participation_score: [0, 100],
  feedback_sentiment_pct: [0, 100],
};

const SEGMENTS = [
  ["Insufficient data", "Critical indicators are missing (<35% completeness or score unavailable); profile cannot be reliably evaluated.", "#94a3b8"],
  ["Multiple support needs", "Student flagged for both academic and placement/attendance support; highest intervention priority.", "#ef4444"],
  ["Low attendance, reasonable academics", "Maintains good academic results despite poor attendance; risk of disengagement or attendance shortage.", "#f59e0b"],
  ["Low academics, adequate attendance", "Attends classes regularly but struggles with academic understanding or exam performance.", "#f97316"],
  ["Strong academics, low placement readiness", "High CGPA/theory knowledge but lacks competitive aptitude, coding, or interview readiness.", "#8b5cf6"],
  ["Strong performance across available indicators", "Excels across academics, attendance, technical skills, and placement preparation.", "#10b981"],
  ["Moderate / Consistent progress", "Satisfactory, balanced progress across available metrics without acute risk triggers.", "#06b6d4"],
];

const round = (n, digits = 1) => Number(Number(n).toFixed(digits));
const val = (row, key) => row[key] === "" || row[key] === undefined ? null : row[key];
const has = (value) => value !== null && value !== undefined && Number.isFinite(Number(value));
const clip = (value) => Math.max(0, Math.min(100, value));
const weighted = (parts) => {
  const present = parts.filter(([value]) => has(value));
  if (!present.length) return null;
  const total = present.reduce((sum, [, weight]) => sum + weight, 0);
  return round(clip(present.reduce((sum, [value, weight]) => sum + Number(value) * weight / total, 0)));
};

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  const input = String(text).replace(/^\uFEFF/, "");
  for (let i = 0; i < input.length; i += 1) {
    const char = input[i];
    if (quoted) {
      if (char === '"' && input[i + 1] === '"') { field += '"'; i += 1; }
      else if (char === '"') quoted = false;
      else field += char;
    } else if (char === '"' && field.length === 0) quoted = true;
    else if (char === ",") { row.push(field); field = ""; }
    else if (char === "\n" || char === "\r") {
      if (char === "\r" && input[i + 1] === "\n") i += 1;
      row.push(field); field = "";
      if (row.some((cell) => cell !== "")) rows.push(row);
      row = [];
    } else field += char;
  }
  if (quoted) throw new Error("CSV contains an unterminated quoted field.");
  if (field.length || row.length) {
    row.push(field);
    if (row.some((cell) => cell !== "")) rows.push(row);
  }
  if (!rows.length) throw new Error("CSV file is empty.");
  const headers = rows.shift().map((header) => header.trim());
  if (headers.some((header) => !header)) throw new Error("CSV contains an empty column name.");
  if (new Set(headers).size !== headers.length) throw new Error("CSV contains duplicate column names.");
  return rows.map((cells, index) => {
    if (cells.length !== headers.length) {
      throw new Error(`CSV row ${index + 2} has ${cells.length} fields; expected ${headers.length}.`);
    }
    const record = {};
    headers.forEach((header, i) => {
      const value = cells[i].trim();
      if (value === "" || value.toLowerCase() === "nan" || value.toLowerCase() === "null") {
        record[header] = null;
      } else if (SCHEMA[header]) {
        const number = Number(value);
        record[header] = Number.isFinite(number) ? number : value;
      } else record[header] = value;
    });
    return record;
  });
}

function csvString(rows, columns) {
  const headers = columns || [...new Set(rows.flatMap((row) => Object.keys(row)))];
  const cell = (value) => {
    if (value === null || value === undefined || Number.isNaN(value)) return "";
    const text = String(value);
    return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  };
  return [headers.map(cell).join(","), ...rows.map((row) => headers.map((key) => cell(row[key])).join(","))].join("\r\n");
}

function validate(rows) {
  const report = {
    total_rows: rows.length, total_cols: rows.length ? Object.keys(rows[0]).length : 0,
    errors: [], warnings: [], missing_summary: {}, duplicate_ids: [], range_violations: [], completeness_avg: 0,
  };
  if (!rows.length) report.errors.push("Uploaded dataset is empty.");
  if (rows.length && !Object.hasOwn(rows[0], "student_id")) report.errors.push("Critical column 'student_id' is missing from the dataset.");
  if (report.errors.length) return report;
  const idCounts = new Map();
  for (const row of rows) idCounts.set(row.student_id, (idCounts.get(row.student_id) || 0) + 1);
  report.duplicate_ids = [...idCounts].filter(([, count]) => count > 1).map(([id]) => String(id));
  if (report.duplicate_ids.length) report.warnings.push(`Found ${report.duplicate_ids.length} duplicate student ID(s): ${report.duplicate_ids.slice(0, 5).join(", ")}${report.duplicate_ids.length > 5 ? "..." : ""}`);
  for (const key of Object.keys(rows[0])) {
    const count = rows.filter((row) => val(row, key) === null).length;
    if (count) report.missing_summary[key] = count;
  }
  for (const [key, [min, max]] of Object.entries(SCHEMA)) {
    const values = rows.map((row) => row[key]).filter(has);
    const below = values.filter((value) => value < min).length;
    const above = values.filter((value) => value > max).length;
    if (below) report.range_violations.push(`Column '${key}' has ${below} values below minimum allowed ${min}.`);
    if (above) report.range_violations.push(`Column '${key}' has ${above} values exceeding maximum allowed ${max}.`);
  }
  report.warnings.push(...report.range_violations);
  const indicators = ["cgpa", "internal_test_pct", "attendance_pct", "lms_assignment_completion_pct", "aptitude_score", "mock_interview_score", "coding_score", "mentor_rating"].filter((key) => Object.hasOwn(rows[0], key));
  report.completeness_avg = indicators.length
    ? round(rows.reduce((sum, row) => sum + indicators.filter((key) => has(row[key])).length / indicators.length * 100, 0) / rows.length)
    : 0;
  return report;
}

function mergeTables(tables) {
  if (!tables.length) throw new Error("Please upload at least one CSV file.");
  const merged = new Map();
  const knownColumns = new Set(["student_id"]);
  for (const [tableIndex, rows] of tables.entries()) {
    if (!rows.length || !Object.hasOwn(rows[0], "student_id")) continue;
    const rename = new Map();
    for (const key of Object.keys(rows[0])) {
      if (key === "student_id") continue;
      let target = key;
      let suffix = tableIndex + 1;
      while (knownColumns.has(target)) {
        target = `${key}_${suffix}`;
        suffix += 1;
      }
      rename.set(key, target);
      knownColumns.add(target);
    }
    const seenIds = new Set();
    for (const row of rows) {
      const id = String(row.student_id);
      if (seenIds.has(id)) continue;
      seenIds.add(id);
      const previous = merged.get(id) || { student_id: id };
      for (const [key, value] of Object.entries(row)) {
        if (key !== "student_id") previous[rename.get(key)] = value;
      }
      merged.set(id, previous);
    }
  }
  if (!merged.size) throw new Error("No uploaded table contains a student_id column.");
  return [...merged.values()];
}

function calculateScore(row, weights = DEFAULT_WEIGHTS) {
  const academicParts = [
    [has(row.cgpa) ? Number(row.cgpa) * 10 : null, 0.7],
    [row.internal_test_pct, 0.3],
  ].filter(([value]) => has(value));
  const academic = academicParts.length
    ? academicParts.reduce((sum, [value, weight]) => sum + Number(value) * weight, 0) / academicParts.reduce((sum, [, weight]) => sum + weight, 0)
    : null;
  const pillars = {
    academic_performance: academic === null ? null : round(clip(academic - (has(row.backlogs) ? Number(row.backlogs) * 5 : 0))),
    attendance: weighted([[row.attendance_pct, 0.7], [row.lab_attendance_pct, 0.3]]),
    lms_completion: weighted([[row.lms_assignment_completion_pct, 0.7], [row.lms_video_watch_pct, 0.3]]),
    placement_readiness: weighted([[row.aptitude_score, 0.5], [row.mock_interview_score, 0.5]]),
    skills_assessment: weighted([[row.coding_score, 0.6], [row.technical_mcq_score, 0.4]]),
    engagement_feedback: weighted([
      [has(row.mentor_rating) ? Number(row.mentor_rating) * 20 : null, 0.5],
      [row.club_participation_score, 0.25], [row.feedback_sentiment_pct, 0.25],
    ]),
  };
  if (pillars.skills_assessment !== null) pillars.skills_assessment = round(clip(pillars.skills_assessment + Math.min(6, Number(row.certifications_count || 0) * 2)));
  const valid = Object.entries(pillars).filter(([, score]) => score !== null);
  const totalWeight = valid.reduce((sum, [key]) => sum + Number(weights[key] || 0), 0);
  const effectiveWeights = Object.fromEntries(Object.keys(PILLARS).map((key) => [key, totalWeight > 0 && pillars[key] !== null ? round(Number(weights[key] || 0) / totalWeight, 4) : 0]));
  const score = valid.length
    ? round(clip(valid.reduce((sum, [key, value]) => sum + value * (totalWeight > 0 ? Number(weights[key] || 0) / totalWeight : 1 / valid.length), 0)))
    : null;
  const ordered = valid.slice().sort((a, b) => a[1] - b[1]);
  const completeness = round(valid.length / Object.keys(PILLARS).length * 100);
  const steps = valid.length
    ? [`Valid Indicators: ${valid.length}/6 (${completeness}% complete)`, "Weighted contributions:", ...valid.map(([key, value]) => `  ${PILLARS[key]}: ${value.toFixed(1)} x ${(effectiveWeights[key] * 100).toFixed(1)}% = ${(value * effectiveWeights[key]).toFixed(2)}`), ...(valid.length < 6 ? ["Missing indicators were excluded; remaining weights were re-normalized."] : []), `Final Success Score = ${score.toFixed(1)} / 100.0`].join("\n")
    : "No valid indicator data found for this student. Score unavailable.";
  return { score, completeness, pillars, effectiveWeights, strongest: ordered.length ? ordered.at(-1)[0] : null, weakest: ordered.length ? ordered[0][0] : null, steps };
}

function assessAcademic(row, th) {
  if (![row.cgpa, row.attendance_pct, row.pillar_academic].some(has)) return ["Insufficient data", "No academic or attendance records available to evaluate academic progress."];
  const critical = []; const review = [];
  if (has(row.cgpa)) {
    if (row.cgpa < th.academic_cgpa_critical) critical.push(`CGPA (${Number(row.cgpa).toFixed(2)}) is below critical threshold of ${th.academic_cgpa_critical}`);
    else if (row.cgpa < th.academic_cgpa_warning) review.push(`CGPA (${Number(row.cgpa).toFixed(2)}) is below target threshold of ${th.academic_cgpa_warning}`);
  }
  if (has(row.backlogs)) {
    if (row.backlogs >= th.academic_backlogs_critical) critical.push(`Active backlogs (${Math.trunc(row.backlogs)}) exceed critical limit of ${th.academic_backlogs_critical}`);
    else if (row.backlogs > 0) review.push(`Student has ${Math.trunc(row.backlogs)} active backlog requiring remedial action`);
  }
  if (has(row.attendance_pct)) {
    if (row.attendance_pct < th.academic_attendance_critical) critical.push(`Attendance (${Number(row.attendance_pct).toFixed(1)}%) is critically below mandatory ${th.academic_attendance_critical}%`);
    else if (row.attendance_pct < th.academic_attendance_warning) review.push(`Attendance (${Number(row.attendance_pct).toFixed(1)}%) is below recommended ${th.academic_attendance_warning}% guideline`);
  }
  if (has(row.pillar_academic)) {
    if (row.pillar_academic < th.academic_score_critical) critical.push(`Composite Academic Pillar score (${Number(row.pillar_academic).toFixed(1)}/100) is in critical zone`);
    else if (row.pillar_academic < th.academic_score_warning) review.push(`Composite Academic Pillar score (${Number(row.pillar_academic).toFixed(1)}/100) requires monitoring`);
  }
  return critical.length ? ["Support recommended", critical.join("; ")] : review.length ? ["Needs review", review.join("; ")] : ["On track", "Academic metrics and attendance meet or exceed benchmark standards."];
}

function assessPlacement(row, th) {
  if (![row.aptitude_score, row.mock_interview_score, row.coding_score, row.pillar_placement].some(has)) return ["Insufficient data", "No placement assessments, mock interview, or coding test data found."];
  const critical = []; const review = [];
  const checks = [
    ["aptitude_score", th.placement_aptitude_critical, th.placement_aptitude_warning, (v, t) => `Aptitude test score (${v.toFixed(1)}%) is below readiness threshold ${t}%`, (v, t) => `Aptitude test score (${v.toFixed(1)}%) is below competitive benchmark ${t}%`],
    ["mock_interview_score", th.placement_interview_critical, th.placement_interview_warning, (v, t) => `Mock interview performance (${v.toFixed(1)}%) needs intensive coaching (<${t}%)`, (v, t) => `Mock interview performance (${v.toFixed(1)}%) is below target ${t}%`],
    ["coding_score", th.placement_coding_critical, th.placement_coding_warning, (v, t) => `Coding test score (${v.toFixed(1)}%) indicates critical hands-on gaps (<${t}%)`, (v, t) => `Coding test score (${v.toFixed(1)}%) needs further practice (<${t}%)`],
    ["pillar_placement", th.placement_score_critical, th.placement_score_warning, (v) => `Overall Placement Pillar score (${v.toFixed(1)}/100) indicates significant risk`, (v) => `Overall Placement Pillar score (${v.toFixed(1)}/100) shows room for improvement`],
  ];
  for (const [key, criticalLimit, warning, criticalMessage, reviewMessage] of checks) {
    if (!has(row[key])) continue;
    const value = Number(row[key]);
    if (value < criticalLimit) critical.push(criticalMessage(value, criticalLimit));
    else if (value < warning) review.push(reviewMessage(value, warning));
  }
  return critical.length ? ["Support recommended", critical.join("; ")] : review.length ? ["Needs review", review.join("; ")] : ["On track", "Placement readiness benchmarks and technical assessments are on target."];
}

function classifySegment(row) {
  const { success_score: score, data_completeness_pct: completeness = 100, academic_risk_status: acad = "On track", placement_risk_status: place = "On track" } = row;
  if (!has(score) || completeness < 35 || (acad === "Insufficient data" && place === "Insufficient data")) return SEGMENTS[0][0];
  if (acad === "Support recommended" && place === "Support recommended") return SEGMENTS[1][0];
  if (has(row.backlogs) && row.backlogs >= 2 && has(row.attendance_pct) && row.attendance_pct < 65 && has(row.aptitude_score) && row.aptitude_score < 50) return SEGMENTS[1][0];
  if (has(row.attendance_pct) && row.attendance_pct < 75 && ((has(row.cgpa) && row.cgpa >= 7) || (has(row.pillar_academic) && row.pillar_academic >= 65))) return SEGMENTS[2][0];
  if (has(row.attendance_pct) && row.attendance_pct >= 75 && ((has(row.cgpa) && row.cgpa < 6) || (has(row.backlogs) && row.backlogs >= 2) || (has(row.pillar_academic) && row.pillar_academic < 55))) return SEGMENTS[3][0];
  const strongAcademic = (has(row.cgpa) && row.cgpa >= 7.5) || (has(row.pillar_academic) && row.pillar_academic >= 75);
  const lowPlacement = place === "Support recommended" || (has(row.pillar_placement) && row.pillar_placement < 60) || (has(row.aptitude_score) && row.aptitude_score < 55) || (has(row.mock_interview_score) && row.mock_interview_score < 50);
  if (strongAcademic && lowPlacement) return SEGMENTS[4][0];
  if (score >= 75 && (!has(row.attendance_pct) || row.attendance_pct >= 78) && (!has(row.pillar_placement) || row.pillar_placement >= 70) && (!has(row.pillar_academic) || row.pillar_academic >= 75)) return SEGMENTS[5][0];
  return SEGMENTS[6][0];
}

function recommendations(row) {
  const recs = [];
  const add = (category, priority, title, trigger_reason, recommended_action, expected_outcome) => recs.push({ category, priority, title, trigger_reason, recommended_action, expected_outcome });
  const score = row.success_score; const completeness = Number(row.data_completeness_pct ?? 100);
  if (!has(score) || completeness < 60) {
    const missing = [["cgpa", "Academics/CGPA"], ["attendance_pct", "Attendance"], ["lms_assignment_completion_pct", "LMS Activities"], ["aptitude_score", "Placement Assessments"], ["mock_interview_score", "Placement Assessments"], ["coding_score", "Technical Skills"]].filter(([key]) => !has(row[key])).map(([, name]) => name);
    add("Data Quality & Assessment Sync", "High", "Complete Missing Profile Assessments & Data Sync", `Profile completeness is currently ${completeness.toFixed(1)}%. Missing data detected in: ${[...new Set(missing)].join(", ") || "Key pillars"}.`, "Schedule makeup diagnostic assessments for missing modules and check LMS/exam portal synchronization.", "Accurate, unpenalized Student Success Score and complete diagnostic clarity.");
  }
  if (has(row.attendance_pct) && row.attendance_pct < 75) {
    const critical = row.attendance_pct < 65;
    add("Attendance & Engagement", critical ? "Urgent" : "Medium", critical ? "Mandatory Faculty Advisor Attendance Check-In & Action Plan" : "Attendance Monitoring & Early Warning Check",
      critical ? `Overall attendance (${row.attendance_pct.toFixed(1)}%) is below critical 65% university detention threshold.` : `Overall attendance (${row.attendance_pct.toFixed(1)}%) is below recommended 75% guideline.`,
      critical ? "Schedule immediate 1-on-1 advisor counseling, notify guardian, and establish bi-weekly attendance check-ins." : "Set up automated weekly attendance notifications and identify recurring scheduling or health conflicts.",
      critical ? "Prevent exam debarment and restore attendance above the mandatory 75% cutoff." : "Sustain attendance above 75% before end-of-semester cutoff.");
  }
  const backlogs = has(row.backlogs) ? Math.trunc(row.backlogs) : 0;
  if (backlogs > 0 || (has(row.cgpa) && row.cgpa < 6.5 && has(row.internal_test_pct) && row.internal_test_pct < 55)) {
    add("Academic Remediation", backlogs >= 2 || (has(row.cgpa) && row.cgpa < 5.5) ? "High" : "Medium", "Targeted Remedial Subject Tutoring & Backlog Clearance Plan", `Student has ${backlogs} active backlog(s) and CGPA of ${has(row.cgpa) ? row.cgpa.toFixed(2) : "N/A"}.`, "Pair student with a subject faculty mentor and peer study circle for specific backlog subjects; provide curated revision question banks.", "Clear pending backlogs during next supplementary cycle and elevate SGPA by 0.5+ points.");
  }
  if (has(row.lms_assignment_completion_pct) && row.lms_assignment_completion_pct < 70) add("LMS & Assignments", "Medium", "Structured Assignment Catch-Up Milestone Schedule", `LMS assignment completion rate (${row.lms_assignment_completion_pct.toFixed(1)}%) falls short of 75% benchmark.`, "Assign weekly modular assignment deadlines with grace periods; track LMS login frequency.", "Improve continuous internal evaluation marks and bridge course homework backlog.");
  if (has(row.aptitude_score) && row.aptitude_score < 60) add("Placement Readiness", row.aptitude_score < 50 ? "High" : "Medium", "Quantitative Aptitude & Logical Reasoning Practice Track", `Placement aptitude test score (${row.aptitude_score.toFixed(1)}%) is below competitive placement threshold (65%).`, "Enroll in campus placement aptitude bootcamp; complete 30 daily timed practice sets on quantitative and logical reasoning.", "Pass preliminary company aptitude screening rounds with 70%+ percentile.");
  if (has(row.coding_score) && row.coding_score < 55) add("Technical Skill Development", row.coding_score < 45 ? "High" : "Medium", "Hands-on Data Structures & Coding Accelerator", `Coding assessment score (${row.coding_score.toFixed(1)}%) indicates practical implementation gaps.`, "Assign curated 50-problem foundational DSA problem roadmap (arrays, strings, search, sort); participate in weekly college coding contests.", "Achieve consistent passing scores on coding assessment filters for technical roles.");
  if (has(row.mock_interview_score) && row.mock_interview_score < 60) add("Interview Preparation", row.mock_interview_score < 50 ? "High" : "Medium", "Mock Technical & HR Interview Simulation Clinic", `Mock interview evaluation score (${row.mock_interview_score.toFixed(1)}%) indicates need for communication and answer structuring practice.`, "Conduct two simulated 45-minute mock interviews using STAR technique; refine resume project bullet points.", "Increase confidence and interview performance score to 75%+.");
  if (!recs.length && has(score) && score >= 78) add("Advanced Enrichment & Leadership", "Low", "Peer Mentorship Role & Tier-1 Placement Fast-Track", `Student maintains high overall Success Score (${score.toFixed(1)}/100) with solid performance across indicators.`, "Invite student to serve as junior peer tutor; fast-track for national hackathons, research projects, and premium dream-tier placements.", "Maximize top-tier placement offers and foster peer leadership.");
  if (!recs.length) add("Continuous Monitoring", "Low", "Maintain Balanced Study Schedule & Skill Portfolio", "Performance across all monitored pillars remains steady within acceptable tolerances.", "Continue regular coursework, stay updated on LMS tasks, and attend weekly placement prep sessions.", "Sustain consistent academic and career readiness progress.");
  return recs;
}

function processDataset(rows, weights = DEFAULT_WEIGHTS, thresholds = DEFAULT_THRESHOLDS) {
  return rows.map((source) => {
    const row = { ...source };
    const result = calculateScore(row, weights);
    Object.assign(row, {
      success_score: result.score, data_completeness_pct: result.completeness,
      strongest_pillar: result.strongest, weakest_pillar: result.weakest,
      pillar_academic: result.pillars.academic_performance,
      pillar_attendance: result.pillars.attendance,
      pillar_lms: result.pillars.lms_completion,
      pillar_placement: result.pillars.placement_readiness,
      pillar_skills: result.pillars.skills_assessment,
      pillar_engagement: result.pillars.engagement_feedback,
      pillars: result.pillars, effective_weights: result.effectiveWeights, calculation_steps: result.steps,
    });
    const [academicStatus, academicReasons] = assessAcademic(row, thresholds);
    const [placementStatus, placementReasons] = assessPlacement(row, thresholds);
    row.academic_risk_status = academicStatus;
    row.academic_risk_reasons = academicReasons;
    row.placement_risk_status = placementStatus;
    row.placement_risk_reasons = placementReasons;
    row.overall_support_flag = academicStatus === "Insufficient data" && placementStatus === "Insufficient data" ? "Insufficient Data"
      : academicStatus === "Support recommended" && placementStatus === "Support recommended" ? "Dual Support Needed"
        : academicStatus === "Support recommended" ? "Academic Support Priority"
          : placementStatus === "Support recommended" ? "Placement Support Priority"
            : academicStatus === "Needs review" || placementStatus === "Needs review" ? "Review Recommended" : "On Track";
    row.student_segment = classifySegment(row);
    row.recommendations = recommendations(row);
    return row;
  });
}

function mergeExport(rows, type) {
  if (type === "raw") return rows;
  const columns = type === "academic"
    ? ["student_id", "name", "department", "semester", "cgpa", "backlogs", "attendance_pct", "success_score", "academic_risk_status", "academic_risk_reasons"]
    : type === "placement"
      ? ["student_id", "name", "department", "semester", "aptitude_score", "mock_interview_score", "coding_score", "success_score", "placement_risk_status", "placement_risk_reasons"]
      : ["student_id", "name", "department", "semester", "gender", "cgpa", "backlogs", "attendance_pct", "lms_assignment_completion_pct", "aptitude_score", "mock_interview_score", "coding_score", "mentor_rating", "data_completeness_pct", "success_score", "academic_risk_status", "placement_risk_status", "overall_support_flag", "student_segment", "strongest_pillar", "weakest_pillar"];
  const selected = type === "academic" ? rows.filter((row) => ["Support recommended", "Needs review"].includes(row.academic_risk_status))
    : type === "placement" ? rows.filter((row) => ["Support recommended", "Needs review"].includes(row.placement_risk_status)) : rows;
  const sorted = selected.slice();
  if (type === "academic") sorted.sort((a, b) => (a.cgpa ?? Infinity) - (b.cgpa ?? Infinity));
  if (type === "placement") sorted.sort((a, b) => (a.aptitude_score ?? Infinity) - (b.aptitude_score ?? Infinity));
  return sorted.map((row) => Object.fromEntries(columns.filter((key) => Object.hasOwn(row, key)).map((key) => [key, row[key]])));
}

module.exports = { DEFAULT_WEIGHTS, DEFAULT_THRESHOLDS, PILLARS, SEGMENTS, SCHEMA, parseCsv, csvString, validate, mergeTables, calculateScore, recommendations, processDataset, mergeExport };
