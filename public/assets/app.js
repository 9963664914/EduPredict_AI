const NAV = [
  ["dashboard", "📊 Executive Dashboard"],
  ["explorer", "🔍 Student Explorer"],
  ["segments", "🏷️ Cohort Segmentation"],
  ["interventions", "💡 Intervention Center"],
  ["data", "📂 Data Integration & Upload"],
  ["settings", "⚙️ Configurable Weights"],
  ["reports", "📑 Reports & Methodology"],
];
const PILLARS = {
  academic_performance: "Academic Performance", attendance: "Attendance",
  lms_completion: "LMS & Digital Learning", placement_readiness: "Placement Readiness",
  skills_assessment: "Technical Skills", engagement_feedback: "Engagement & Feedback",
};
const WEIGHT_NAMES = Object.keys(PILLARS);
const THRESHOLD_INFO = [
  ["academic_cgpa_critical", "Critical CGPA", 0, 10, 0.1],
  ["academic_cgpa_warning", "CGPA review target", 0, 10, 0.1],
  ["academic_attendance_critical", "Critical attendance (%)", 0, 100, 1],
  ["academic_attendance_warning", "Attendance review target (%)", 0, 100, 1],
  ["academic_backlogs_critical", "Critical backlog count", 0, 10, 1],
  ["academic_score_critical", "Critical academic pillar score", 0, 100, 1],
  ["academic_score_warning", "Academic pillar review target", 0, 100, 1],
  ["placement_aptitude_critical", "Critical aptitude score", 0, 100, 1],
  ["placement_aptitude_warning", "Aptitude review target", 0, 100, 1],
  ["placement_interview_critical", "Critical interview score", 0, 100, 1],
  ["placement_interview_warning", "Interview review target", 0, 100, 1],
  ["placement_coding_critical", "Critical coding score", 0, 100, 1],
  ["placement_coding_warning", "Coding review target", 0, 100, 1],
  ["placement_score_critical", "Critical placement pillar score", 0, 100, 1],
  ["placement_score_warning", "Placement pillar review target", 0, 100, 1],
];
const state = { authenticated: false, user: null, rows: [], report: null, weights: {}, thresholds: {}, page: "dashboard", filters: { department: [], semester: [], academic: [], placement: [], segment: [], search: "" }, selectedId: "", selectedSegment: "Insufficient data", uploadMode: "single", message: null };
const app = document.getElementById("app");
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const fmt = (value, digits = 1) => value === null || value === undefined || !Number.isFinite(Number(value)) ? "N/A" : Number(value).toFixed(digits);
const pct = (num, total) => total ? `${(100 * num / total).toFixed(1)}%` : "0%";

async function api(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.error || `Request failed (${response.status}).`);
    error.payload = payload;
    throw error;
  }
  return payload;
}

function setMessage(text, kind = "success") {
  state.message = { text, kind };
  render();
}

async function loadState() {
  const data = await api("/api/state");
  Object.assign(state, data, { authenticated: true });
  state.filters = state.filters || { department: [], semester: [], academic: [], placement: [], segment: [], search: "" };
  render();
}

function badge(text) {
  let tone = "slate";
  if (text === "On track" || text === "Low") tone = "green";
  else if (text === "Needs review" || text === "Medium") tone = "amber";
  else if (text === "Support recommended" || text === "Urgent" || text === "High" || text === "Dual Support Needed") tone = "red";
  else if (text === "Insufficient data") tone = "slate";
  else if (text === "Placement Support Priority") tone = "purple";
  return `<span class="badge ${tone}">${esc(text || "N/A")}</span>`;
}

function allUnique(key) {
  return [...new Set(state.rows.map((row) => row[key]).filter((value) => value !== null && value !== undefined && value !== ""))].sort((a, b) => String(a).localeCompare(String(b)));
}

function filterSelect(title, key, options) {
  const selected = state.filters[key] || [];
  return `<div class="filter-group"><label for="filter-${key}">${esc(title)}</label><select id="filter-${key}" data-filter="${key}" multiple size="${Math.min(4, Math.max(2, options.length))}">${options.map((option) => `<option value="${esc(option)}" ${selected.includes(option) ? "selected" : ""}>${esc(option)}</option>`).join("")}</select></div>`;
}

function shell() {
  const user = state.user || {};
  return `<div class="app-shell">
    <aside class="sidebar" id="sidebar">
      <div class="brand"><div class="brand-icon">🎓</div><div><strong>EduPredict AI</strong><small>byteXL HacXLerate 2026 · KPMG</small></div></div>
      <div class="user-card"><div class="user-avatar">${esc(user.avatar || "👤")}</div><div><strong>${esc(user.name || "User")}</strong><small>${esc(user.role || "Faculty")}</small></div></div>
      <div class="nav-title">WORKSPACE</div><nav class="nav">${NAV.map(([key, label]) => `<button type="button" data-page="${key}" class="${state.page === key ? "active" : ""}">${label}</button>`).join("")}</nav>
      <div class="toolbar"><button class="signout" type="button" data-action="logout">🚪 Sign Out</button></div><hr>
      <div class="filters"><div class="filter-title">GLOBAL COHORT FILTERS</div>
        ${filterSelect("Department", "department", allUnique("department"))}
        ${filterSelect("Semester", "semester", allUnique("semester"))}
        ${filterSelect("Academic support flag", "academic", ["On track", "Needs review", "Support recommended", "Insufficient data"])}
        ${filterSelect("Placement support flag", "placement", ["On track", "Needs review", "Support recommended", "Insufficient data"])}
        ${filterSelect("Student segment", "segment", state.segments || [])}
        <div class="filter-group"><label for="filter-search">Search ID or name</label><input id="filter-search" class="search-input" data-search placeholder="e.g. STU0014 or Sharma" value="${esc(state.filters.search || "")}"></div>
        <button class="button small" data-action="clear-filters" type="button">Clear filters</button>
        <p class="disclaimer"><b>Advisory disclaimer:</b><br>Scores are transparent prototype indicators. Human review is required for all academic actions.</p>
      </div>
    </aside>
    <main class="main"><div class="topline"><button class="button small mobile-toggle" data-action="toggle-sidebar">☰ Menu</button><span>${esc(user.role || "Institutional analytics workspace")}</span><span>${state.rows.length} records loaded</span></div>
      ${state.message ? `<div class="status ${esc(state.message.kind)}" role="status">${esc(state.message.text)}<button data-action="dismiss-message" aria-label="Dismiss" style="float:right;border:0;background:transparent;color:inherit">×</button></div>` : ""}
      ${renderPage()}
    </main>
  </div>`;
}

function getFilteredRows() {
  const f = state.filters;
  const q = (f.search || "").trim().toLowerCase();
  return state.rows.filter((row) =>
    (!f.department.length || f.department.includes(row.department)) &&
    (!f.semester.length || f.semester.includes(row.semester)) &&
    (!f.academic.length || f.academic.includes(row.academic_risk_status)) &&
    (!f.placement.length || f.placement.includes(row.placement_risk_status)) &&
    (!f.segment.length || f.segment.includes(row.student_segment)) &&
    (!q || String(row.student_id || "").toLowerCase().includes(q) || String(row.name || "").toLowerCase().includes(q))
  );
}

function pageHeading(title, description) {
  return `<header class="page-heading"><h1>${title}</h1><p>${description}</p></header>`;
}

function metric(title, value, hint, tone = "") {
  return `<div class="metric ${tone}"><div class="metric-label">${title}</div><div class="metric-value">${value}</div><div class="metric-hint">${hint}</div></div>`;
}

function mean(rows, key, digits = 1) {
  const values = rows.map((row) => row[key]).filter((value) => value !== null && value !== undefined && Number.isFinite(Number(value)));
  return values.length ? Number((values.reduce((sum, value) => sum + Number(value), 0) / values.length).toFixed(digits)) : null;
}

function histogram(rows) {
  const scored = rows.map((row) => row.success_score).filter((v) => v !== null && Number.isFinite(Number(v)));
  if (!scored.length) return emptyChart("No available scores");
  const bins = Array(10).fill(0);
  scored.forEach((score) => { bins[Math.min(9, Math.floor(Number(score) / 10))] += 1; });
  const max = Math.max(...bins, 1); const left = 38; const top = 20; const width = 550; const height = 190; const gap = 8; const barW = (width - gap * 9) / 10;
  const bars = bins.map((value, i) => {
    const h = value / max * 150; const x = left + i * (barW + gap); const y = top + 160 - h;
    return `<rect class="bar" x="${x}" y="${y}" width="${barW}" height="${h}" rx="4"><title>${i * 10}-${i * 10 + 9}: ${value} students</title></rect><text x="${x + barW / 2}" y="198" text-anchor="middle">${i * 10}</text>`;
  }).join("");
  return `<svg class="chart" viewBox="0 0 620 235" role="img" aria-label="Student score distribution"><line class="gridline" x1="38" y1="180" x2="590" y2="180"/><line class="gridline" x1="38" y1="100" x2="590" y2="100"/>${bars}<text x="10" y="28">Students</text><text x="540" y="221">Score</text></svg>`;
}

function emptyChart(message) {
  return `<div class="empty">${esc(message)}</div>`;
}

function scatter(rows) {
  const points = rows.filter((row) => Number.isFinite(Number(row.pillar_academic)) && Number.isFinite(Number(row.pillar_placement)));
  if (!points.length) return emptyChart("No academic and placement pairs available");
  const circle = points.map((row) => {
    const x = 48 + Number(row.pillar_academic) * 5.1; const y = 205 - Number(row.pillar_placement) * 1.65;
    const risky = row.academic_risk_status === "Support recommended" || row.placement_risk_status === "Support recommended";
    return `<circle class="dot ${risky ? "risk" : ""}" cx="${x}" cy="${y}" r="4"><title>${esc(row.student_id)} · Academic ${fmt(row.pillar_academic)} · Placement ${fmt(row.pillar_placement)}</title></circle>`;
  }).join("");
  return `<svg class="chart" viewBox="0 0 600 250" role="img" aria-label="Academic and placement scores"><line class="axis" x1="48" y1="205" x2="558" y2="205"/><line class="axis" x1="48" y1="40" x2="48" y2="205"/><line class="gridline" x1="48" y1="105" x2="558" y2="105"/><line class="gridline" x1="303" y1="40" x2="303" y2="205"/>${circle}<text x="220" y="238">Academic pillar score</text><text x="8" y="35">Placement</text><text x="32" y="210">0</text><text x="32" y="44">100</text><text x="48" y="221">0</text><text x="543" y="221">100</text></svg>`;
}

function departmentChart(rows) {
  const groups = groupBy(rows, "department");
  const entries = Object.entries(groups).map(([name, group]) => [name, mean(group, "success_score")]).filter(([, value]) => value !== null).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return emptyChart("No department score data available");
  return `<div class="pillar-list">${entries.map(([name, score]) => `<div class="pillar-row"><span>${esc(name)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(0, Math.min(100, score))}%"></div></div><b>${fmt(score)}</b></div>`).join("")}</div>`;
}

function groupBy(rows, key) {
  return rows.reduce((groups, row) => {
    const value = row[key] || "Unavailable";
    (groups[value] ||= []).push(row);
    return groups;
  }, {});
}

function segmentChart(rows) {
  const groups = groupBy(rows, "student_segment");
  const values = Object.entries(groups).sort((a, b) => b[1].length - a[1].length);
  if (!values.length) return emptyChart("No segments to display");
  const colors = Object.fromEntries((state.segments || []).map((name, i) => [name, ["#94a3b8", "#ef4444", "#f59e0b", "#f97316", "#8b5cf6", "#10b981", "#06b6d4"][i]]));
  const total = rows.length || 1; let offset = 0;
  const arcs = values.map(([name, group]) => {
    const start = offset; const end = offset + group.length / total * 100; offset = end;
    return `<circle cx="100" cy="100" r="68" fill="none" stroke="${colors[name] || "#22d3ee"}" stroke-width="25" stroke-dasharray="${group.length / total * 427} ${427 - group.length / total * 427}" stroke-dashoffset="${-start / 100 * 427}" transform="rotate(-90 100 100)"><title>${esc(name)}: ${group.length}</title></circle>`;
  }).join("");
  const legend = values.map(([name, group]) => `<div class="segment-legend" style="display:flex;gap:7px;align-items:center;margin:7px 0"><span style="width:9px;height:9px;border-radius:50%;background:${colors[name] || "#22d3ee"}"></span><span>${esc(name)}</span><b style="margin-left:auto">${group.length}</b></div>`).join("");
  return `<div style="display:grid;grid-template-columns:minmax(150px,1fr) minmax(160px,1.3fr);align-items:center"><svg viewBox="0 0 200 200" style="width:100%;max-height:230px">${arcs}<text x="100" y="104" text-anchor="middle" style="fill:#f8fafc;font-size:20px;font-weight:700">${rows.length}</text></svg><div>${legend}</div></div>`;
}

function table(rows, columns, limit = 100) {
  if (!rows.length) return emptyChart("No records match the current filters.");
  const shown = rows.slice(0, limit);
  return `<div class="table-wrap"><table><thead><tr>${columns.map(([key, label]) => `<th>${esc(label)}</th>`).join("")}</tr></thead><tbody>${shown.map((row) => `<tr>${columns.map(([key]) => `<td>${tableValue(row, key)}</td>`).join("")}</tr>`).join("")}</tbody></table></div><div class="table-footer">Showing ${shown.length} of ${rows.length} records</div>`;
}

function tableValue(row, key) {
  const value = row[key];
  if (key === "success_score") return fmt(value);
  if (key === "cgpa") return fmt(value, 2);
  if (key.includes("attendance") || key.includes("pct")) return value === null || value === undefined ? "N/A" : `${fmt(value)}%`;
  if (key.endsWith("_status") || key === "overall_support_flag") return badge(value);
  if (key === "student_segment") return esc(value);
  return esc(value ?? "N/A");
}

function dashboard(rows) {
  const scored = rows.map((row) => row.success_score).filter((value) => value !== null);
  const avgScore = scored.length ? (scored.reduce((sum, value) => sum + value, 0) / scored.length).toFixed(1) : "N/A";
  const academic = rows.filter((row) => row.academic_risk_status === "Support recommended").length;
  const placement = rows.filter((row) => row.placement_risk_status === "Support recommended").length;
  const dual = rows.filter((row) => row.overall_support_flag === "Dual Support Needed").length;
  const strong = rows.filter((row) => row.student_segment === "Strong performance across available indicators").length;
  const gap = rows.filter((row) => row.student_segment === "Strong academics, low placement readiness").length;
  return `${pageHeading("📊 Executive Student Success Dashboard", "Real-time analytics across Academic, Attendance, LMS, Skills, and Placement dimensions.")}
    ${!rows.length ? emptyChart("No student records match the active filter criteria. Adjust your sidebar filters.") : `
      <div class="metrics">${metric("Total Cohort", rows.length, "Active student records")}${metric("Avg Success Score", avgScore, "0–100 normalized index", "cyan")}${metric("Academic Support", academic, `${pct(academic, rows.length)} of filtered cohort`, "red")}${metric("Placement Support", placement, `${pct(placement, rows.length)} of filtered cohort`, "purple")}${metric("Avg Attendance / CGPA", `${fmt(mean(rows, "attendance_pct"))}% / ${fmt(mean(rows, "cgpa"), 2)}`, "Overall institutional health", "green")}</div>
      <div class="notice"><b>💡 Automated Diagnostic Insights</b><ul><li><b>${dual}</b> student(s) require concurrent academic and placement intervention.</li><li><b>${gap}</b> student(s) demonstrate strong academics but lag in placement readiness.</li><li><b>${strong}</b> student(s) excel across available indicators.</li></ul></div>
      <div class="grid-2"><section class="panel"><h2>📈 Success Score Distribution</h2>${histogram(rows)}</section><section class="panel"><h2>🎯 Academic vs Placement Readiness</h2>${scatter(rows)}</section></div>
      <div class="grid-2"><section class="panel"><h2>🏛️ Average Score by Department</h2>${departmentChart(rows)}</section><section class="panel"><h2>🏷️ Cohort Segmentation</h2>${segmentChart(rows)}</section></div>
    `}`;
}

function explorer(rows) {
  if (!rows.length) return `${pageHeading("🔍 Student Explorer", "Explore detailed student scores, support factors, and recommendations.")}${emptyChart("No student records match the current filters.")}`;
  const selected = rows.find((row) => row.student_id === state.selectedId) || rows[0];
  state.selectedId = selected.student_id;
  const pillars = selected.pillars || {};
  const pillarRows = Object.entries(PILLARS).map(([key, title]) => `<div class="pillar-row"><span>${esc(title)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(0, Math.min(100, pillars[key] || 0))}%"></div></div><b>${pillars[key] === null ? "N/A" : fmt(pillars[key])}</b></div>`).join("");
  const recs = (window.currentStudentRecs = getRecommendations(selected));
  return `${pageHeading("🔍 Individual Student Explorer", "Inspect student score breakdowns, redistributed weights, and explainable interventions.")}
    ${table(rows, [["student_id", "Student ID"], ["name", "Name"], ["department", "Department"], ["semester", "Semester"], ["cgpa", "CGPA"], ["backlogs", "Backlogs"], ["attendance_pct", "Attendance"], ["success_score", "Success score"], ["academic_risk_status", "Academic risk"], ["placement_risk_status", "Placement risk"], ["student_segment", "Segment"]], 100)}
    <section class="panel" style="margin-top:16px"><h2>Student Diagnostic Profile</h2><div class="field"><label for="student-select">Select a student</label><select id="student-select" class="search-input">${rows.map((row) => `<option value="${esc(row.student_id)}" ${row.student_id === selected.student_id ? "selected" : ""}>${esc(row.student_id)} — ${esc(row.name)} (${esc(row.department)})</option>`).join("")}</select></div>
      <div class="student-header"><div class="student-card"><strong>${esc(selected.name || "Unknown")}</strong><span>${esc(selected.student_id)} · ${esc(selected.department || "N/A")} · ${esc(selected.semester || "N/A")}</span></div><div class="student-card"><span>SUCCESS SCORE</span><span class="big">${fmt(selected.success_score)}<small>/100</small></span></div><div class="student-card"><span>DATA COMPLETENESS</span><span class="big">${fmt(selected.data_completeness_pct)}%</span></div><div class="student-card"><span>SEGMENT</span><p>${esc(selected.student_segment)}</p></div></div>
      <div class="grid-2"><div class="panel"><h3>⚖️ Pillar Breakdown & Effective Weights</h3><div class="pillar-list">${pillarRows}</div><p>Strongest: ${badge(PILLARS[selected.strongest_pillar] || "None")} &nbsp; Weakest: ${badge(PILLARS[selected.weakest_pillar] || "None")}</p></div><div class="panel"><h3>Calculation transparency</h3><pre style="white-space:pre-wrap;color:#cbd5e1;font:12px/1.7 ui-monospace,monospace">${esc(selected.calculation_steps)}</pre><h3>Effective weights</h3>${Object.entries(PILLARS).map(([key, title]) => `<div class="pillar-row"><span>${esc(title)}</span><div class="bar-track"><div class="bar-fill" style="width:${(selected.effective_weights[key] || 0) * 100}%"></div></div><b>${((selected.effective_weights[key] || 0) * 100).toFixed(1)}%</b></div>`).join("")}</div></div>
      <h2>Independent Support Evaluation</h2><div class="grid-2"><div class="risk-card"><b>Academic evaluation ${badge(selected.academic_risk_status)}</b><p>${esc(selected.academic_risk_reasons)}</p></div><div class="risk-card"><b>Placement evaluation ${badge(selected.placement_risk_status)}</b><p>${esc(selected.placement_risk_reasons)}</p></div></div>
      <h2>🎯 Explainable Action Plan & Recommended Interventions</h2>${recs.map(recommendationCard).join("")}
    </section>`;
}

function getRecommendations(row) {
  if (Array.isArray(row.recommendations)) return row.recommendations;
  const missing = !Number.isFinite(Number(row.success_score)) || row.data_completeness_pct < 60;
  const result = [];
  if (missing) result.push({ category: "Data Quality & Assessment Sync", priority: "High", title: "Complete Missing Profile Assessments & Data Sync", trigger_reason: `Profile completeness is ${fmt(row.data_completeness_pct)}%.`, recommended_action: "Schedule makeup diagnostic assessments and check LMS/exam portal synchronization.", expected_outcome: "Accurate score and complete diagnostic clarity." });
  if (Number.isFinite(Number(row.attendance_pct)) && row.attendance_pct < 75) result.push({ category: "Attendance & Engagement", priority: row.attendance_pct < 65 ? "Urgent" : "Medium", title: row.attendance_pct < 65 ? "Mandatory Faculty Advisor Attendance Check-In & Action Plan" : "Attendance Monitoring & Early Warning Check", trigger_reason: `Overall attendance is ${fmt(row.attendance_pct)}%, below the recommended 75% guideline.`, recommended_action: "Schedule advisor check-ins and establish weekly attendance monitoring.", expected_outcome: "Restore attendance above the 75% cutoff." });
  if (Number(row.backlogs) > 0) result.push({ category: "Academic Remediation", priority: row.backlogs >= 2 ? "High" : "Medium", title: "Targeted Remedial Subject Tutoring & Backlog Clearance Plan", trigger_reason: `Student has ${row.backlogs} active backlog(s) and CGPA ${fmt(row.cgpa, 2)}.`, recommended_action: "Pair the student with a subject faculty mentor and peer study circle.", expected_outcome: "Clear pending backlogs and improve academic progress." });
  if (row.lms_assignment_completion_pct != null && row.lms_assignment_completion_pct < 70) result.push({ category: "LMS & Assignments", priority: "Medium", title: "Structured Assignment Catch-Up Milestone Schedule", trigger_reason: `LMS assignment completion is ${fmt(row.lms_assignment_completion_pct)}%.`, recommended_action: "Set weekly assignment milestones and track LMS activity.", expected_outcome: "Improve coursework completion." });
  if (row.aptitude_score != null && row.aptitude_score < 60) result.push({ category: "Placement Readiness", priority: row.aptitude_score < 50 ? "High" : "Medium", title: "Quantitative Aptitude & Logical Reasoning Practice Track", trigger_reason: `Aptitude test score is ${fmt(row.aptitude_score)}%, below the competitive threshold.`, recommended_action: "Enroll in aptitude bootcamp and complete timed practice sets.", expected_outcome: "Improve placement screening readiness." });
  if (row.coding_score != null && row.coding_score < 55) result.push({ category: "Technical Skill Development", priority: row.coding_score < 45 ? "High" : "Medium", title: "Hands-on Data Structures & Coding Accelerator", trigger_reason: `Coding assessment score is ${fmt(row.coding_score)}%.`, recommended_action: "Follow a foundational DSA practice roadmap and attend coding contests.", expected_outcome: "Improve practical coding assessment scores." });
  if (row.mock_interview_score != null && row.mock_interview_score < 60) result.push({ category: "Interview Preparation", priority: row.mock_interview_score < 50 ? "High" : "Medium", title: "Mock Technical & HR Interview Simulation Clinic", trigger_reason: `Mock interview score is ${fmt(row.mock_interview_score)}%.`, recommended_action: "Schedule mock interviews using the STAR technique and refine resume projects.", expected_outcome: "Improve interview readiness." });
  if (!result.length) result.push({ category: "Continuous Monitoring", priority: "Low", title: "Maintain Balanced Study Schedule & Skill Portfolio", trigger_reason: "Performance across monitored indicators remains steady.", recommended_action: "Continue regular coursework and weekly placement preparation.", expected_outcome: "Sustain academic and career readiness." });
  return result;
}

function recommendationCard(rec) {
  return `<div class="rec-card ${esc(rec.priority.toLowerCase())}"><div class="rec-title"><span>${esc(rec.title)}</span>${badge(rec.priority)}</div><p><b>Trigger:</b> ${esc(rec.trigger_reason)}<br><b>Action:</b> ${esc(rec.recommended_action)}<br><b>Outcome:</b> ${esc(rec.expected_outcome)}</p></div>`;
}

function segmentsPage(rows) {
  const stats = (state.segments || []).map((name) => {
    const members = rows.filter((row) => row.student_segment === name);
    return { name, members, avg: mean(members, "success_score") };
  });
  const selected = stats.find((item) => item.name === state.selectedSegment) || stats[0];
  if (selected) state.selectedSegment = selected.name;
  const members = selected ? selected.members : [];
  return `${pageHeading("🏷️ Student Cohort Segmentation", "Mutually distinct student groups classified using deterministic, transparent precedence rules.")}
    <div class="grid-2"><section class="panel"><h2>Segment Distribution Overview</h2>${table(stats.map((item) => ({ segment: item.name, count: item.members.length, percentage: rows.length ? (item.members.length / rows.length * 100).toFixed(1) : "0.0", average_score: item.avg })), [["segment", "Segment"], ["count", "Students"], ["percentage", "Share (%)"], ["average_score", "Average score"]])}</section><section class="panel"><h2>Segment distribution</h2>${segmentChart(rows)}</section></div>
    <section class="panel"><h2>Segment Drill-Down & Student Roster</h2><div class="field"><label for="segment-select">Choose a segment</label><select id="segment-select" class="search-input">${stats.map((item) => `<option ${item.name === state.selectedSegment ? "selected" : ""} value="${esc(item.name)}">${esc(item.name)}</option>`).join("")}</select></div>${selected ? `<div class="notice"><b>${esc(selected.name)}</b> · Priority ${stats.indexOf(selected) + 1}<br>${esc((state.segmentDescriptions || {})[selected.name] || "")}</div><p>${members.length} student(s)</p>${table(members, [["student_id", "Student ID"], ["name", "Name"], ["department", "Department"], ["semester", "Semester"], ["cgpa", "CGPA"], ["attendance_pct", "Attendance"], ["aptitude_score", "Aptitude"], ["success_score", "Success score"], ["academic_risk_status", "Academic risk"], ["placement_risk_status", "Placement risk"]])}` : ""}</section>`;
}

function interventionsPage(rows) {
  const counts = new Map();
  for (const row of rows) for (const rec of getRecommendations(row)) counts.set(rec.title, (counts.get(rec.title) || 0) + 1);
  const summary = [...counts].sort((a, b) => b[1] - a[1]).map(([title, count]) => ({ title, count, share: pct(count, rows.length) }));
  const urgent = rows.filter((row) => ["Dual Support Needed", "Academic Support Priority"].includes(row.overall_support_flag));
  return `${pageHeading("💡 Institutional Intervention Center", "Data-driven action plans to allocate mentoring, remedial tutoring, and placement support.")}
    <div class="grid-2"><section class="panel"><h2>📈 Highest Demand Interventions</h2>${table(summary, [["title", "Intervention action"], ["count", "Students"], ["share", "Cohort share"]])}</section><section class="panel"><h2>🚨 Urgent Priority Action List</h2><p>${urgent.length} student(s) flagged for urgent advisory intervention.</p>${table(urgent, [["student_id", "ID"], ["name", "Name"], ["department", "Department"], ["cgpa", "CGPA"], ["attendance_pct", "Attendance"], ["overall_support_flag", "Priority"]])}</section></div>
    <section class="panel"><h2>Support cohort worklist</h2>${table(rows.filter((row) => row.academic_risk_status === "Support recommended" || row.placement_risk_status === "Support recommended"), [["student_id", "ID"], ["name", "Name"], ["student_segment", "Segment"], ["academic_risk_status", "Academic risk"], ["placement_risk_status", "Placement risk"], ["academic_risk_reasons", "Academic trigger"], ["placement_risk_reasons", "Placement trigger"]])}</section>`;
}

function auditMarkup(report) {
  const warnings = report.warnings || [];
  return `<div class="metrics" style="grid-template-columns:repeat(3,minmax(0,1fr))">${metric("Total Records", report.total_rows, "In active dataset")}${metric("Avg Profile Completeness", `${fmt(report.completeness_avg)}%`, "Across available indicators", "cyan")}${metric("Duplicate Student IDs", report.duplicate_ids.length, "Duplicate IDs flagged", report.duplicate_ids.length ? "red" : "green")}</div>
    ${Object.keys(report.missing_summary || {}).length ? `<div class="panel"><h3>Missing values by feature</h3>${table(Object.entries(report.missing_summary).map(([feature, count]) => ({ feature, count })), [["feature", "Feature"], ["count", "Missing values"]])}</div>` : ""}
    ${warnings.length ? `<div class="status warning"><b>Data quality warnings</b><ul>${warnings.map((warning) => `<li>${esc(warning)}</li>`).join("")}</ul></div>` : `<div class="status success">No range violations or duplicate student IDs detected.</div>`}`;
}

function dataPage() {
  const report = state.report || {};
  return `${pageHeading("📂 Data Integration, Upload & Schema Validation", "Upload one complete CSV or multiple departmental files joined by student ID.")}
    <div class="panel"><h2>Upload student CSV data</h2><p class="panel-subtitle">CSV files remain in this application session; required identifier: student_id.</p>
      <div class="toolbar"><label><input type="radio" name="upload-mode" value="single" ${state.uploadMode === "single" ? "checked" : ""}> Single unified CSV</label><label><input type="radio" name="upload-mode" value="multiple" ${state.uploadMode === "multiple" ? "checked" : ""}> Multiple tables joined by student_id</label></div>
      <form id="upload-form"><div class="field"><label for="csv-file">${state.uploadMode === "single" ? "Choose unified student CSV" : "Choose departmental CSV files (select multiple)"}</label><input id="csv-file" name="files" type="file" accept=".csv,text/csv" ${state.uploadMode === "multiple" ? "multiple" : ""} required></div>
      <button class="button primary" type="submit">${state.uploadMode === "multiple" ? "Merge & Validate Tables" : "Upload & Validate Dataset"}</button></form>
      <div class="template-list">${(state.templates || []).map((name) => `<a href="/templates/${encodeURIComponent(name)}" download>⬇ ${esc(name)}</a>`).join("")}</div>
    </div>
    <section class="panel" style="margin-top:15px"><h2>📋 Active Dataset Validation Audit</h2>${auditMarkup(report)}<div class="toolbar"><button class="button danger" type="button" data-action="reset">🔄 Reset to Default 100-Student Dataset</button></div></section>`;
}

function settingsPage() {
  return `${pageHeading("⚙️ Configurable Weights & Risk Thresholds", "Changes are saved to your session and recalculate every student score and support flag.")}
    <form id="settings-form"><div class="settings-group"><h3>1. Indicator Pillar Weights (normalized to 100%)</h3><div class="form-grid">${WEIGHT_NAMES.map((key) => `<div class="field"><label for="weight-${key}">${esc(PILLARS[key])} <span data-weight-label="${key}">${((state.weights[key] || 0) * 100).toFixed(0)}%</span></label><input id="weight-${key}" name="weight-${key}" data-weight="${key}" type="range" min="0" max="50" step="5" value="${Math.round((state.weights[key] || 0) * 100)}"></div>`).join("")}</div><p class="panel-subtitle">Set at least one weight above zero.</p></div>
    <div class="settings-group"><h3>2. Academic and placement decision thresholds</h3><div class="form-grid">${THRESHOLD_INFO.map(([key, label, min, max, step]) => `<div class="field"><label for="th-${key}">${esc(label)} <span data-th-label="${key}">${fmt(state.thresholds[key], step < 1 ? 1 : 0)}</span></label><input id="th-${key}" name="th-${key}" data-threshold="${key}" type="range" min="${min}" max="${max}" step="${step}" value="${state.thresholds[key]}"></div>`).join("")}</div></div>
    <div class="toolbar"><button class="button primary" type="submit">Apply Scoring Weights & Thresholds</button><button class="button" type="button" data-action="default-settings">Reset to defaults</button></div></form>`;
}

const methodology = `<section class="panel"><h2>Formal Methodology & Ethical Guidelines</h2>
  <h3>Prototype scope</h3><p>Student Success Scores and risk indicators are transparent heuristic metrics, not validated predictors of academic failure or placement outcomes. Qualified faculty review all insights.</p>
  <h3>Six indicator pillars</h3><ul><li><b>Academic Performance (25%)</b> — normalized CGPA (70%) + internal tests (30%); 5-point deduction per backlog.</li><li><b>Attendance (20%)</b> — class attendance (70%) + lab attendance (30%).</li><li><b>LMS Engagement (15%)</b> — assignment completion (70%) + video completion (30%).</li><li><b>Placement Readiness (20%)</b> — aptitude (50%) + mock interview (50%).</li><li><b>Skills Assessment (10%)</b> — coding (60%) + technical MCQ (40%) + certification bonus.</li><li><b>Engagement & Feedback (10%)</b> — mentor rating (50%) + club participation (25%) + sentiment (25%).</li></ul>
  <h3>Missing data and re-normalization</h3><p>Missing indicators are never silently replaced with zero. Available pillar weights are re-normalized to 100%. Profiles with no usable indicators show “Unavailable”.</p>
  <h3>Independent risk assessment</h3><p>Academic and placement support are assessed independently and include the recorded triggering factors. Statuses include On track, Needs review, Support recommended, and Insufficient data.</p>
  <h3>Responsible use</h3><ul><li>Support flags are advisory, not disciplinary or automated disqualification decisions.</li><li>Student records should remain access-controlled and comply with applicable privacy guidelines.</li><li>Every indicator is explainable and requires a human-in-the-loop review.</li></ul>
</section>`;

function reportsPage(rows) {
  const reportTypes = [
    ["scored", "📊 Export Scored Cohort CSV", "edupredict_scored_cohort.csv"],
    ["academic", "📚 Export Academic Support List", "academic_support_roster.csv"],
    ["placement", "💼 Export Placement Support List", "placement_support_roster.csv"],
    ["raw", "📄 Export Raw Filtered CSV", "edupredict_filtered_raw.csv"],
  ];
  return `${pageHeading("📑 Reports, Exports & Methodology", "Download audit-ready cohort reports and review the scoring approach and ethical safeguards.")}
    <section class="panel"><h2>📥 Instant CSV Downloads</h2><p class="panel-subtitle">Exports reflect active cohort filters. Academic/placement rosters include both support recommendations and review cases.</p><div class="template-list">${reportTypes.map(([type, label, filename]) => `<button class="button" data-export="${type}" data-filename="${filename}">${label}</button>`).join("")}</div></section>
    ${methodology}`;
}

function renderPage() {
  const rows = getFilteredRows();
  switch (state.page) {
    case "explorer": return explorer(rows);
    case "segments": return segmentsPage(rows);
    case "interventions": return interventionsPage(rows);
    case "data": return dataPage();
    case "settings": return settingsPage();
    case "reports": return reportsPage(rows);
    default: return dashboard(rows);
  }
}

function loginScreen(error = "") {
  return `<main class="login-wrap"><section class="login"><div class="login-brand"><div class="login-icon">🎓</div><h1>EduPredict AI</h1><p>Smarter Insights. Transparent Evaluation. Actionable Support.</p><small>byteXL HacXLerate 2026 | Problem Statement 4 by KPMG in India</small></div>
    ${error ? `<div class="status error">${esc(error)}</div>` : ""}
    <form id="login-form"><h3>🔐 Institutional Sign In</h3><div class="field"><label for="username">Username</label><input id="username" name="username" autocomplete="username" placeholder="e.g. admin, advisor, tpo, hod" required></div><div class="field"><label for="password">Password</label><input id="password" name="password" type="password" autocomplete="current-password" placeholder="Enter account password" required></div><button class="button primary" type="submit">Sign In to Platform</button></form>
    <div class="credentials"><p class="nav-title" style="text-align:center">⚡ QUICK DEMO ACCESS</p><div class="demo-buttons">${[["admin", "👑 Dean / Admin"], ["advisor", "📚 Academic Advisor"], ["tpo", "💼 Placement Officer"], ["hod", "🏛️ Dept Head (HOD)"]].map(([user, label]) => `<button class="button" type="button" data-demo="${user}">${label}</button>`).join("")}</div>
    <details class="credentials"><summary>View demo account credentials</summary><table><thead><tr><th>Role</th><th>Username</th><th>Password</th></tr></thead><tbody><tr><td>Dean / Administrator</td><td>admin</td><td>admin@2026</td></tr><tr><td>Academic Advisor</td><td>advisor</td><td>advisor@2026</td></tr><tr><td>Placement Officer</td><td>tpo</td><td>tpo@2026</td></tr><tr><td>Department Head</td><td>hod</td><td>hod@2026</td></tr></tbody></table></details></div>
  </section></main>`;
}

function render() {
  app.innerHTML = state.authenticated ? shell() : loginScreen(state.loginError || "");
}

async function login(username, password) {
  try {
    state.loginError = "";
    const result = await api("/api/login", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ username, password }) });
    state.user = result.user;
    state.authenticated = true;
    state.page = "dashboard";
    state.message = null;
    await loadState();
  } catch (error) {
    state.loginError = error.message;
    render();
  }
}

function downloadCsv(rows, filename) {
  if (!rows.length) {
    setMessage("There are no records to export for the current selection.", "warning");
    return;
  }
  const cols = [...new Set(rows.flatMap((row) => Object.keys(row)))].filter((key) => !["pillars", "effective_weights", "calculation_steps"].includes(key));
  const cell = (value) => {
    if (value === null || value === undefined || typeof value === "object") return "";
    const text = String(value);
    return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  };
  const csv = [cols.join(","), ...rows.map((row) => cols.map((key) => cell(row[key])).join(","))].join("\r\n");
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8" }));
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

function exportRows(type) {
  const rows = getFilteredRows();
  let selected = rows;
  let filename = "";
  if (type === "academic") {
    selected = rows.filter((row) => ["Support recommended", "Needs review"].includes(row.academic_risk_status)).sort((a, b) => (a.cgpa ?? Infinity) - (b.cgpa ?? Infinity));
    filename = "academic_support_roster.csv";
  } else if (type === "placement") {
    selected = rows.filter((row) => ["Support recommended", "Needs review"].includes(row.placement_risk_status)).sort((a, b) => (a.aptitude_score ?? Infinity) - (b.aptitude_score ?? Infinity));
    filename = "placement_support_roster.csv";
  } else if (type === "scored") {
    const keys = ["student_id", "name", "department", "semester", "gender", "cgpa", "backlogs", "attendance_pct", "lms_assignment_completion_pct", "aptitude_score", "mock_interview_score", "coding_score", "mentor_rating", "data_completeness_pct", "success_score", "academic_risk_status", "placement_risk_status", "overall_support_flag", "student_segment", "strongest_pillar", "weakest_pillar"];
    selected = rows.map((row) => Object.fromEntries(keys.filter((key) => Object.hasOwn(row, key)).map((key) => [key, row[key]])));
    filename = "edupredict_scored_cohort.csv";
  } else filename = "edupredict_filtered_raw.csv";
  downloadCsv(selected, filename);
}

app.addEventListener("click", async (event) => {
  const pageButton = event.target.closest("[data-page]");
  if (pageButton) { state.page = pageButton.dataset.page; state.message = null; render(); return; }
  const demo = event.target.closest("[data-demo]");
  if (demo) { login(demo.dataset.demo, `${demo.dataset.demo}@2026`); return; }
  const exportButton = event.target.closest("[data-export]");
  if (exportButton) { exportRows(exportButton.dataset.export); return; }
  const action = event.target.closest("[data-action]")?.dataset.action;
  if (!action) return;
  if (action === "dismiss-message") { state.message = null; render(); }
  if (action === "toggle-sidebar") document.getElementById("sidebar").classList.toggle("open");
  if (action === "clear-filters") {
    state.filters = { department: [], semester: [], academic: [], placement: [], segment: [], search: "" };
    render();
  }
  if (action === "logout") {
    await api("/api/logout", { method: "POST" });
    state.authenticated = false; state.user = null; state.rows = []; state.page = "dashboard"; state.message = null; render();
  }
  if (action === "reset") {
    if (!window.confirm("Restore the default dataset? Current scoring settings will be kept.")) return;
    try { const result = await api("/api/reset", { method: "POST" }); await loadState(); state.message = { text: result.message, kind: "success" }; render(); }
    catch (error) { setMessage(error.message, "error"); }
  }
  if (action === "default-settings") {
    try {
      await api("/api/settings", { method: "PUT", headers: { "content-type": "application/json" }, body: JSON.stringify({ weights: { academic_performance: .25, attendance: .2, lms_completion: .15, placement_readiness: .2, skills_assessment: .1, engagement_feedback: .1 }, thresholds: { academic_cgpa_critical: 6, academic_cgpa_warning: 7, academic_attendance_critical: 65, academic_attendance_warning: 75, academic_backlogs_critical: 2, academic_score_critical: 55, academic_score_warning: 65, placement_aptitude_critical: 50, placement_aptitude_warning: 65, placement_interview_critical: 50, placement_interview_warning: 65, placement_coding_critical: 45, placement_coding_warning: 60, placement_score_critical: 50, placement_score_warning: 65 } }) });
      await loadState(); state.message = { text: "Default weights and thresholds restored.", kind: "success" }; render();
    } catch (error) { setMessage(error.message, "error"); }
  }
});

app.addEventListener("change", async (event) => {
  if (event.target.matches("[data-filter]")) {
    state.filters[event.target.dataset.filter] = [...event.target.selectedOptions].map((option) => option.value);
    render();
  }
  if (event.target.id === "student-select") { state.selectedId = event.target.value; render(); }
  if (event.target.id === "segment-select") { state.selectedSegment = event.target.value; render(); }
  if (event.target.name === "upload-mode") { state.uploadMode = event.target.value; render(); }
  if (event.target.matches("[data-weight]")) {
    const label = document.querySelector(`[data-weight-label="${event.target.dataset.weight}"]`);
    if (label) label.textContent = `${event.target.value}%`;
  }
  if (event.target.matches("[data-threshold]")) {
    const label = document.querySelector(`[data-th-label="${event.target.dataset.threshold}"]`);
    if (label) label.textContent = event.target.value;
  }
});

app.addEventListener("input", (event) => {
  if (event.target.matches("[data-search]")) {
    state.filters.search = event.target.value;
    const cursor = event.target.selectionStart;
    render();
    const input = document.getElementById("filter-search");
    input.focus(); input.setSelectionRange(cursor, cursor);
  }
});

app.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (event.target.id === "login-form") {
    const form = new FormData(event.target);
    await login(form.get("username"), form.get("password"));
  } else if (event.target.id === "upload-form") {
    const fileInput = document.getElementById("csv-file");
    if (!fileInput.files.length) { setMessage("Choose at least one CSV file.", "warning"); return; }
    const form = new FormData();
    [...fileInput.files].forEach((file) => form.append("files", file));
    try {
      const result = await api("/api/upload", { method: "POST", body: form });
      await loadState(); state.page = "data"; state.message = { text: result.message, kind: "success" }; render();
    } catch (error) {
      const details = error.payload?.report?.errors?.join(" ") || error.message;
      setMessage(details, "error");
    }
  } else if (event.target.id === "settings-form") {
    const weights = Object.fromEntries(WEIGHT_NAMES.map((key) => [key, Number(event.target.elements[`weight-${key}`].value)]));
    const thresholds = Object.fromEntries(THRESHOLD_INFO.map(([key]) => [key, Number(event.target.elements[`th-${key}`].value)]));
    try {
      await api("/api/settings", { method: "PUT", headers: { "content-type": "application/json" }, body: JSON.stringify({ weights, thresholds }) });
      await loadState(); state.page = "settings"; state.message = { text: "Settings applied and scores recalculated.", kind: "success" }; render();
    } catch (error) { setMessage(error.message, "error"); }
  }
});

api("/api/session").then((result) => {
  if (result.authenticated) {
    state.authenticated = true;
    state.user = result.user;
    return loadState();
  }
  render();
}).catch((error) => {
  app.innerHTML = `<div class="login-wrap"><div class="login"><h1>Unable to connect</h1><p>${esc(error.message)}</p><button class="button" onclick="location.reload()">Retry</button></div></div>`;
});
