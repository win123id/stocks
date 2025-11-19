from flask import Flask, request, jsonify, send_from_directory
import os

from data import load_tickers_from_json, download_history
from scanners import (
    scan_golden_cross_for_tickers,
    scan_llv_sma50_value_for_tickers,
    scan_mode4_combo_for_tickers,
    scan_lower_low_3days_for_tickers,
)

app = Flask(__name__)


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(app.root_path, "favicon.ico", mimetype="image/vnd.microsoft.icon")

@app.route("/scan", methods=["GET"])
def scan():

    # Get query params
    path = request.args.get("file", "idx80.json")
    mode = request.args.get("mode", "1")

    # Resolve file path
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(__file__), path)

    tickers = load_tickers_from_json(path)
    if not tickers:
        return jsonify({"error": "No tickers found"}), 400

    label = os.path.basename(path)

    # Call scanners based on mode
    if mode == "2":
        result = scan_llv_sma50_value_for_tickers(
            tickers,
            llv_window=5,
            sma_period=50,
            near_low=0.99,
            near_high=1.02,
            min_value=1e9,
            label=label,
        )

    elif mode == "3":
        result = scan_llv_sma50_value_for_tickers(
            tickers,
            llv_window=5,
            sma_period=200,
            near_low=0.99,
            near_high=1.02,
            min_value=1e9,
            label=label,
        )

    elif mode == "4":
        result = scan_mode4_combo_for_tickers(tickers, label=label)

    elif mode == "5":
        result = scan_lower_low_3days_for_tickers(tickers, label=label)

    else:
        result = scan_golden_cross_for_tickers(tickers, label=label)

    return jsonify({"status": "ok", "data": result})


@app.route("/")
def home():
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Python Stock Scanner</title>
  <link rel="icon" type="image/x-icon" href="/favicon.ico" />
  <style>
    :root {
      color-scheme: dark;
      --bg: #020617;
      --bg-elevated: #020617;
      --panel: #020617;
      --accent: #38bdf8;
      --accent-soft: rgba(56, 189, 248, 0.15);
      --accent-strong: #0ea5e9;
      --border-subtle: rgba(148, 163, 184, 0.35);
      --text-main: #e5e7eb;
      --text-muted: #9ca3af;
      --danger: #f97373;
    }
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text-main);
      background:
        radial-gradient(circle at top left, rgba(56,189,248,0.15), transparent 55%),
        radial-gradient(circle at bottom right, rgba(129,140,248,0.18), transparent 55%),
        var(--bg);
      display: flex;
      align-items: stretch;
      justify-content: center;
    }
    .shell {
      width: 100%;
      max-width: 1120px;
      margin: 32px 16px;
      border-radius: 20px;
      border: 1px solid rgba(148, 163, 184, 0.3);
      background: radial-gradient(circle at top left, rgba(17,24,39,0.9), rgba(15,23,42,0.96));
      box-shadow:
        0 24px 60px rgba(15, 23, 42, 0.9),
        0 0 0 1px rgba(15, 23, 42, 0.6);
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .header {
      padding: 20px 24px 12px;
      border-bottom: 1px solid rgba(148, 163, 184, 0.2);
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      gap: 6px 16px;
    }
    .title {
      font-size: 20px;
      font-weight: 600;
      letter-spacing: 0.02em;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .chip {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      padding: 2px 8px;
      border-radius: 999px;
      background: rgba(34, 197, 94, 0.1);
      border: 1px solid rgba(34, 197, 94, 0.45);
      color: #bbf7d0;
    }
    .subtitle {
      color: var(--text-muted);
      font-size: 13px;
    }
    .content {
      display: grid;
      grid-template-columns: minmax(0, 340px) minmax(0, 1fr);
      gap: 0;
      min-height: 420px;
    }
    @media (max-width: 900px) {
      .content {
        display: block;
      }
      .sidebar {
        border-right: none;
        border-bottom: 1px solid rgba(148, 163, 184, 0.2);
      }
    }
    .sidebar {
      padding: 18px 20px 20px;
      border-right: 1px solid rgba(148, 163, 184, 0.2);
      background: radial-gradient(circle at top left, rgba(15,23,42,0.9), rgba(15,23,42,0.98));
    }
    .field-label {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
      margin-bottom: 6px;
    }
    .input, .select {
      width: 100%;
      border-radius: 10px;
      border: 1px solid var(--border-subtle);
      padding: 9px 11px;
      font-size: 13px;
      color: var(--text-main);
      background: rgba(15,23,42,0.9);
      outline: none;
      transition: border-color 120ms ease, box-shadow 120ms ease, background 120ms ease;
    }
    .input::placeholder {
      color: rgba(148, 163, 184, 0.7);
    }
    .input:focus, .select:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.35);
      background: rgba(15,23,42,1);
    }
    .row {
      margin-bottom: 14px;
    }
    .hint {
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 4px;
    }
    .modes {
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-top: 6px;
      margin-bottom: 10px;
      font-size: 12px;
      color: var(--text-muted);
    }
    .mode-pill {
      padding: 6px 8px;
      border-radius: 10px;
      border: 1px solid rgba(148, 163, 184, 0.3);
      background: radial-gradient(circle at top left, rgba(15,23,42,0.7), rgba(15,23,42,0.95));
    }
    .mode-pill strong {
      color: var(--accent-strong);
      font-weight: 500;
      margin-right: 4px;
    }
    .actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 12px;
    }
    .btn {
      border-radius: 999px;
      padding: 9px 18px;
      border: none;
      font-size: 13px;
      font-weight: 500;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: #0b1120;
      background: linear-gradient(135deg, var(--accent), var(--accent-strong));
      box-shadow:
        0 10px 30px rgba(56, 189, 248, 0.4),
        0 0 0 1px rgba(8, 47, 73, 0.9);
      transition: transform 100ms ease, box-shadow 100ms ease, opacity 80ms ease;
    }
    .btn span.dot {
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: rgba(15,23,42,0.85);
    }
    .btn:hover {
      transform: translateY(-1px);
      box-shadow:
        0 16px 40px rgba(56, 189, 248, 0.45),
        0 0 0 1px rgba(8, 47, 73, 1);
    }
    .btn:active {
      transform: translateY(0);
      box-shadow:
        0 8px 22px rgba(15, 23, 42, 0.9),
        0 0 0 1px rgba(15, 23, 42, 0.9);
    }
    .btn:disabled {
      opacity: 0.6;
      cursor: default;
      box-shadow:
        0 8px 22px rgba(15, 23, 42, 0.7),
        0 0 0 1px rgba(15, 23, 42, 0.9);
      transform: none;
    }
    .status {
      font-size: 11px;
      color: var(--text-muted);
    }
    .status--error {
      color: #fecaca;
    }
    .status--ok {
      color: #bbf7d0;
    }
    .status--loading {
      color: #e5e7eb;
    }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(15,23,42,0.9);
      border: 1px solid rgba(148,163,184,0.35);
    }
    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 999px;
      background: rgba(248,250,252,0.4);
    }
    .status--ok .status-dot {
      background: #22c55e;
    }
    .status--error .status-dot {
      background: #f97373;
    }
    .status--loading .status-dot {
      background: #eab308;
    }
    .results-panel {
      padding: 18px 20px 20px;
      background: radial-gradient(circle at top right, rgba(15,23,42,0.9), rgba(15,23,42,0.98));
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .results-header {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
    }
    .results-title {
      font-size: 13px;
      font-weight: 500;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: rgba(148, 163, 184, 0.9);
      text-align: center;
    }
    .results-meta {
      font-size: 11px;
      color: var(--text-muted);
      text-align: center;
    }
    .results-container {
      flex: 1;
      min-height: 260px;
      border-radius: 12px;
      border: 1px solid rgba(148, 163, 184, 0.3);
      background: radial-gradient(circle at top left, rgba(15,23,42,0.9), rgba(15,23,42,0.98));
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .results-scroll {
      flex: 1;
      overflow: auto;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }
    thead {
      position: sticky;
      top: 0;
      background: rgba(15,23,42,0.98);
      box-shadow: 0 1px 0 rgba(30, 64, 175, 0.7);
      z-index: 1;
    }
    th, td {
      padding: 8px 10px;
      text-align: center;
      white-space: nowrap;
    }
    th {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: rgba(148, 163, 184, 0.95);
    }
    tbody tr:nth-child(even) {
      background: rgba(15,23,42,0.85);
    }
    tbody tr:nth-child(odd) {
      background: rgba(15,23,42,0.95);
    }
    tbody tr:hover {
      background: rgba(30,64,175,0.65);
    }
    td {
      border-top: 1px solid rgba(30, 64, 175, 0.7);
      color: rgba(226, 232, 240, 0.96);
    }
    td.numeric {
      text-align: center;
      font-variant-numeric: tabular-nums;
    }
    .empty-state {
      padding: 24px;
      font-size: 13px;
      color: var(--text-muted);
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="header">
      <div class="title">
        Python Stock Scanner
        <span class="chip">Live API</span>
      </div>
      <div class="subtitle">
        Run technical scans over your JSON ticker lists with a single click.
      </div>
    </div>
    <div class="content">
      <section class="sidebar">
        <div class="row">
          <div class="field-label">Ticker list (JSON file)</div>
          <select id="file-input" class="select">
            <option value="idx30.json">IDX30 (idx30.json)</option>
            <option value="idx80.json" selected>IDX80 (idx80.json)</option>
            <option value="kompas100.json">Kompas100 (kompas100.json)</option>
          </select>
          <div class="hint">Files are resolved relative to the server folder.</div>
        </div>
        <div class="row">
          <div class="field-label">Scan mode</div>
          <select id="mode-input" class="select">
            <option value="1">1 – 20/50 MA golden cross</option>
            <option value="2">2 – LLV(5) &gt; SMA50, near SMA50, value &gt; 1B</option>
            <option value="3">3 – LLV(5) &gt; SMA200, near SMA200, value &gt; 1B</option>
            <option value="4">4 – Trend + squeeze + MACD + RSI combo</option>
            <option value="5">5 – 3 consecutive lower daily lows</option>
          </select>
          <div class="modes">
            <div class="mode-pill"><strong>1</strong> Recent 20/50 MA golden crosses.</div>
            <div class="mode-pill"><strong>2</strong> Around SMA50 with volume filter.</div>
            <div class="mode-pill"><strong>3</strong> Around SMA200 with volume filter.</div>
            <div class="mode-pill"><strong>4</strong> Strong trend + squeeze + MACD + RSI.</div>
            <div class="mode-pill"><strong>5</strong> Three-day lower-low pattern on daily lows.</div>
          </div>
        </div>
        <div class="actions">
          <button id="run-btn" class="btn">
            <span class="dot"></span>
            Run scan
          </button>
          <div id="status" class="status">
            <span class="status-badge status--idle">
              <span class="status-dot"></span>
              Idle
            </span>
          </div>
        </div>
      </section>
      <section class="results-panel">
        <div class="results-header">
          <div class="results-title">Scan results</div>
          <div id="results-meta" class="results-meta">No scan yet.</div>
        </div>
        <div class="results-container">
          <div id="empty-state" class="empty-state">
            Choose a ticker list and scan mode, then click <strong>Run scan</strong>.
          </div>
          <div class="results-scroll" style="display:none;">
            <table>
              <thead>
                <tr id="results-head"></tr>
              </thead>
              <tbody id="results-body"></tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  </div>
  <script>
    const runBtn = document.getElementById("run-btn");
    const fileInput = document.getElementById("file-input");
    const modeInput = document.getElementById("mode-input");
    const statusBox = document.getElementById("status");
    const emptyState = document.getElementById("empty-state");
    const scrollArea = document.querySelector(".results-scroll");
    const headRow = document.getElementById("results-head");
    const bodyEl = document.getElementById("results-body");
    const metaEl = document.getElementById("results-meta");

    function setStatus(kind, text) {
      const cls = kind === "error" ? "status--error" : kind === "ok" ? "status--ok" : "status--loading";
      statusBox.innerHTML = `
        <span class="status-badge ${cls}">
          <span class="status-dot"></span>
          <span>${text}</span>
        </span>
      `;
    }

    function toLabel(key) {
      return key
        .replace(/_/g, " ")
        .replace(/\\b(gc)\\b/i, "GC")
        .replace(/\\b(ma)\\b/i, "MA")
        .replace(/\\b(sma)\\b/i, "SMA")
        .replace(/\\b(llv)\\b/i, "LLV")
        .replace(/\\b(rsi)\\b/i, "RSI")
        .replace(/\\b(macd)\\b/i, "MACD")
        .replace(/\\b(idr)\\b/i, "IDR")
        .replace(/\\b(jk)\\b/i, "JK")
        .replace(/\\b\\w/g, (m) => m.toUpperCase());
    }

    function isNumeric(value) {
      return typeof value === "number";
    }

    function orderKeys(rawKeys) {
      const lower = (k) => String(k).toLowerCase();
      const dateCandidates = ["date", "gc_date"]; // support both "date" and "gc_date"

      const dateKey = rawKeys.find((k) => dateCandidates.includes(lower(k)));
      const symbolKey = rawKeys.find((k) => lower(k) === "symbol");

      const rest = rawKeys.filter((k) => k !== dateKey && k !== symbolKey);

      const ordered = [];
      if (dateKey) ordered.push(dateKey);
      if (symbolKey) ordered.push(symbolKey);
      return ordered.concat(rest);
    }

    function renderResults(data, context) {
      if (!Array.isArray(data) || data.length === 0) {
        emptyState.style.display = "block";
        scrollArea.style.display = "none";
        bodyEl.innerHTML = "";
        headRow.innerHTML = "";
        metaEl.textContent = "No matches for this scan.";
        return;
      }
      emptyState.style.display = "none";
      scrollArea.style.display = "block";

      const keys = orderKeys(Object.keys(data[0]));
      headRow.innerHTML = keys
        .map((k) => `<th>${toLabel(k)}</th>`)
        .join("");

      const rowsHtml = data
        .map((row) => {
          return "<tr>" + keys.map((k) => {
            const v = row[k];
            const cls = isNumeric(v) ? "numeric" : "";
            return `<td class="${cls}">${v == null ? "" : v}</td>`;
          }).join("") + "</tr>";
        })
        .join("");
      bodyEl.innerHTML = rowsHtml;

      metaEl.textContent = "";
    }

    async function runScan() {
      const file = fileInput.value.trim() || "idx80.json";
      const mode = modeInput.value;
      runBtn.disabled = true;
      setStatus("loading", "Running scan...");
      metaEl.textContent = "Running scan...";

      try {
        const url = `/scan?file=${encodeURIComponent(file)}&mode=${encodeURIComponent(mode)}`;
        const response = await fetch(url);
        const payload = await response.json().catch(() => null);

        if (!response.ok) {
          const msg = payload && payload.error ? payload.error : `HTTP ${response.status}`;
          setStatus("error", msg);
          renderResults([], "");
          return;
        }

        if (!payload || (payload.error && !payload.data)) {
          const msg = payload && payload.error ? payload.error : "Unexpected server response.";
          setStatus("error", msg);
          renderResults([], "");
          return;
        }

        const data = payload.data || [];
        const count = Array.isArray(data) ? data.length : 0;
        setStatus("ok", count === 0 ? "Scan completed – no matches." : `Scan completed – ${count} result(s).`);
        renderResults(data, "");
      } catch (err) {
        setStatus("error", "Failed to reach server.");
        renderResults([], "");
      } finally {
        runBtn.disabled = false;
      }
    }

    runBtn.addEventListener("click", (e) => {
      e.preventDefault();
      runScan();
    });

    fileInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        runScan();
      }
    });
  </script>
</body>
</html>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)
