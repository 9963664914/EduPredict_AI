const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const {
  DEFAULT_WEIGHTS, DEFAULT_THRESHOLDS, parseCsv, validate, mergeTables, processDataset,
} = require("./analytics");

const ROOT = __dirname;
const PORT = Number(process.env.PORT || 8501);
const SESSION_COOKIE = "edupredict_session";
const sessions = new Map();
const accounts = {
  admin: { password: "admin@2026", name: "Dr. K. S. Sharma", role: "Dean / Administrator", avatar: "👑" },
  advisor: { password: "advisor@2026", name: "Prof. Sneha Verma", role: "Academic Advisor", avatar: "📚" },
  tpo: { password: "tpo@2026", name: "Mr. Arjun Reddy", role: "Placement Officer (TPO)", avatar: "💼" },
  hod: { password: "hod@2026", name: "Dr. Meera Iyer", role: "Department Head (HOD)", avatar: "🏛️" },
};

function defaultRows() {
  return parseCsv(fs.readFileSync(path.join(ROOT, "data", "synthetic_students.csv"), "utf8"));
}

function sendJson(res, status, value) {
  const body = JSON.stringify(value);
  res.writeHead(status, { "content-type": "application/json; charset=utf-8", "content-length": Buffer.byteLength(body), "cache-control": "no-store" });
  res.end(body);
}

function getSession(req) {
  const cookie = req.headers.cookie || "";
  const match = cookie.match(/(?:^|;\s*)edupredict_session=([a-f0-9]+)/);
  return match ? sessions.get(match[1]) : null;
}

function sendError(res, status, message) {
  sendJson(res, status, { error: message });
}

function readBody(req, limit = 16 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > limit) {
        reject(new Error("Upload exceeds the 16 MB limit."));
        req.destroy();
      } else chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

async function readJson(req) {
  const body = await readBody(req, 1024 * 1024);
  try { return JSON.parse(body.toString("utf8") || "{}"); }
  catch { throw new Error("Request body must contain valid JSON."); }
}

async function readUpload(req) {
  const body = await readBody(req);
  const contentType = req.headers["content-type"] || "";
  if (contentType.includes("application/json")) {
    let payload;
    try { payload = JSON.parse(body.toString("utf8")); }
    catch { throw new Error("Upload request must contain valid JSON."); }
    if (typeof payload.csv !== "string") throw new Error("Choose a CSV file to upload.");
    return [{ name: "student_data.csv", rows: parseCsv(payload.csv) }];
  }
  const boundary = contentType.match(/boundary=(?:"([^"]+)"|([^;]+))/i);
  if (!boundary) throw new Error("Expected a CSV file upload.");
  const marker = `--${boundary[1] || boundary[2]}`;
  const parts = body.toString("latin1").split(marker).slice(1, -1);
  const uploads = [];
  for (const part of parts) {
    const separator = part.indexOf("\r\n\r\n");
    if (separator < 0) continue;
    const headers = part.slice(0, separator);
    const filename = headers.match(/filename="([^"]+)"/i);
    if (!filename) continue;
    const data = part.slice(separator + 4).replace(/\r\n$/, "");
    const csvText = Buffer.from(data, "latin1").toString("utf8");
    uploads.push({ name: path.basename(filename[1]), rows: parseCsv(csvText) });
  }
  if (!uploads.length) throw new Error("Choose one or more CSV files to upload.");
  return uploads;
}

function sendFile(res, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const mime = ext === ".html" ? "text/html; charset=utf-8"
    : ext === ".css" ? "text/css; charset=utf-8"
      : ext === ".js" ? "text/javascript; charset=utf-8"
        : ext === ".csv" ? "text/csv; charset=utf-8" : "application/octet-stream";
  res.writeHead(200, { "content-type": mime, "cache-control": "no-cache" });
  fs.createReadStream(filePath).pipe(res);
}

function stateFor(session) {
  return {
    user: session.user,
    weights: session.weights,
    thresholds: session.thresholds,
    report: validate(session.rows),
    rows: processDataset(session.rows, session.weights, session.thresholds),
    segments: require("./analytics").SEGMENTS.map(([name]) => name),
    segmentDescriptions: Object.fromEntries(require("./analytics").SEGMENTS.map(([name, description]) => [name, description])),
    templates: fs.readdirSync(path.join(ROOT, "data", "templates")).filter((name) => name.endsWith(".csv")),
  };
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  try {
    if (req.method === "GET" && url.pathname === "/") {
      return sendFile(res, path.join(ROOT, "public", "index.html"));
    }
    if (req.method === "GET" && url.pathname.startsWith("/assets/")) {
      const relative = decodeURIComponent(url.pathname.slice("/assets/".length));
      const fullPath = path.resolve(ROOT, "public", "assets", relative);
      if (!fullPath.startsWith(path.resolve(ROOT, "public", "assets") + path.sep)) return sendError(res, 404, "File not found.");
      if (!fs.existsSync(fullPath) || !fs.statSync(fullPath).isFile()) return sendError(res, 404, "File not found.");
      return sendFile(res, fullPath);
    }
    if (req.method === "GET" && url.pathname.startsWith("/templates/")) {
      const name = path.basename(decodeURIComponent(url.pathname.slice("/templates/".length)));
      const fullPath = path.join(ROOT, "data", "templates", name);
      if (!name.endsWith(".csv") || !fs.existsSync(fullPath)) return sendError(res, 404, "Template not found.");
      res.setHeader("content-disposition", `attachment; filename="${name}"`);
      return sendFile(res, fullPath);
    }
    if (req.method === "GET" && url.pathname === "/api/session") {
      const session = getSession(req);
      return session ? sendJson(res, 200, { authenticated: true, user: session.user }) : sendJson(res, 200, { authenticated: false });
    }
    if (req.method === "POST" && url.pathname === "/api/login") {
      const body = await readJson(req);
      const username = String(body.username || "").trim().toLowerCase();
      const account = accounts[username];
      if (!account || account.password !== String(body.password || "")) return sendError(res, 401, "Invalid username or password.");
      const token = crypto.randomBytes(24).toString("hex");
      const session = { user: { username, name: account.name, role: account.role, avatar: account.avatar }, rows: defaultRows(), weights: { ...DEFAULT_WEIGHTS }, thresholds: { ...DEFAULT_THRESHOLDS } };
      sessions.set(token, session);
      res.setHeader("set-cookie", `${SESSION_COOKIE}=${token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800`);
      return sendJson(res, 200, { authenticated: true, user: session.user });
    }
    if (req.method === "POST" && url.pathname === "/api/logout") {
      const cookie = req.headers.cookie || "";
      const match = cookie.match(/(?:^|;\s*)edupredict_session=([a-f0-9]+)/);
      if (match) sessions.delete(match[1]);
      res.setHeader("set-cookie", `${SESSION_COOKIE}=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0`);
      return sendJson(res, 200, { ok: true });
    }
    const session = getSession(req);
    if (url.pathname.startsWith("/api/") && !session) return sendError(res, 401, "Please sign in to continue.");
    if (req.method === "GET" && url.pathname === "/api/state") return sendJson(res, 200, stateFor(session));
    if (req.method === "PUT" && url.pathname === "/api/settings") {
      const body = await readJson(req);
      if (body.weights) {
        const keys = Object.keys(DEFAULT_WEIGHTS);
        if (keys.some((key) => !Number.isFinite(Number(body.weights[key])) || Number(body.weights[key]) < 0)) return sendError(res, 400, "Weights must be non-negative numbers.");
        const total = keys.reduce((sum, key) => sum + Number(body.weights[key]), 0);
        if (total <= 0) return sendError(res, 400, "At least one scoring weight must be greater than zero.");
        session.weights = Object.fromEntries(keys.map((key) => [key, Number(body.weights[key]) / total]));
      }
      if (body.thresholds) {
        for (const [key, value] of Object.entries(body.thresholds)) {
          if (!(key in DEFAULT_THRESHOLDS) || !Number.isFinite(Number(value))) return sendError(res, 400, `Invalid risk threshold: ${key}.`);
        }
        session.thresholds = { ...session.thresholds, ...Object.fromEntries(Object.entries(body.thresholds).map(([key, value]) => [key, Number(value)])) };
      }
      return sendJson(res, 200, { weights: session.weights, thresholds: session.thresholds });
    }
    if (req.method === "POST" && url.pathname === "/api/upload") {
      let uploads;
      try { uploads = await readUpload(req); }
      catch (error) { return sendError(res, 400, error.message); }
      let rows;
      try { rows = uploads.length === 1 ? uploads[0].rows : mergeTables(uploads.map((upload) => upload.rows)); }
      catch (error) { return sendError(res, 422, error.message); }
      const report = validate(rows);
      if (report.errors.length) return sendJson(res, 422, { error: "Validation failed.", report });
      session.rows = rows;
      return sendJson(res, 200, { message: `Loaded ${rows.length} student record(s) from ${uploads.length} CSV file(s).`, report });
    }
    if (req.method === "POST" && url.pathname === "/api/reset") {
      session.rows = defaultRows();
      return sendJson(res, 200, { message: "Default 100-student dataset restored." });
    }
    if (req.method === "GET" && url.pathname.startsWith("/api/")) return sendError(res, 404, "API route not found.");
    return sendError(res, 404, "Page not found.");
  } catch (error) {
    console.error(error);
    if (!res.headersSent) sendError(res, 500, "The request could not be completed. Check the server log for details.");
    else res.end();
  }
});
const HOST = "0.0.0.0";

server.listen(PORT, HOST, () => {
  console.log(`EduPredict AI is running on ${HOST}:${PORT}`);
});

server.on("error", (error) => {
  console.error("Unable to start EduPredict AI:", error.message);
  process.exitCode = 1;
});
