const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {
  DEFAULT_WEIGHTS, calculateScore, parseCsv, csvString, validate, mergeTables, processDataset,
} = require("../analytics");

test("CSV parser preserves quoted commas, quotes, line breaks, and missing values", () => {
  const rows = parseCsv('student_id,name,cgpa,note\r\nS1,"Doe, Jane",8.2,"said ""hello""\nand left"\r\nS2,Ada,,');
  assert.equal(rows[0].name, "Doe, Jane");
  assert.equal(rows[0].note, 'said "hello"\nand left');
  assert.equal(rows[1].cgpa, null);
  assert.equal(parseCsv(csvString(rows))[0].name, "Doe, Jane");
});

test("score recalculates weights for available pillars and leaves unavailable scores null", () => {
  const result = calculateScore({ cgpa: 8, attendance_pct: 80 });
  assert.equal(result.score, 80);
  assert.equal(result.completeness, 33.3);
  assert.equal(result.effectiveWeights.academic_performance, 0.5556);
  assert.equal(result.effectiveWeights.attendance, 0.4444);
  assert.equal(calculateScore({}).score, null);
});

test("validates required ID, duplicate IDs, and feature ranges", () => {
  assert.match(validate([{ name: "No ID" }]).errors[0], /student_id/);
  const report = validate([{ student_id: "S1", cgpa: 11 }, { student_id: "S1", cgpa: 8 }]);
  assert.deepEqual(report.duplicate_ids, ["S1"]);
  assert.equal(report.range_violations.length, 1);
});

test("merges tables on student ID without discarding unmatched rows", () => {
  const rows = mergeTables([
    [{ student_id: "S1", name: "Ada" }],
    [{ student_id: "S1", cgpa: 8, name: "Ada Updated" }, { student_id: "S2", cgpa: 6 }],
  ]);
  assert.equal(rows.length, 2);
  assert.equal(rows.find((row) => row.student_id === "S1").cgpa, 8);
  assert.equal(rows.find((row) => row.student_id === "S1").name_2, "Ada Updated");
  assert.equal(rows.find((row) => row.student_id === "S2").name, undefined);
});

test("processes the demonstration cohort and adds risk, segment, and actionable recommendations", () => {
  const csv = fs.readFileSync(path.join(__dirname, "..", "data", "synthetic_students.csv"), "utf8");
  const rows = processDataset(parseCsv(csv), DEFAULT_WEIGHTS);
  assert.equal(rows.length, 100);
  assert.ok(rows.every((row) => row.success_score === null || (row.success_score >= 0 && row.success_score <= 100)));
  assert.ok(rows.every((row) => row.student_segment && Array.isArray(row.recommendations)));
  assert.ok(rows.some((row) => row.academic_risk_status === "Support recommended"));
});
