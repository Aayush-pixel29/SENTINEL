"""Builds a self-contained modern HTML dashboard from report JSON."""


def build_html(report_json_str: str) -> str:
    """Return a complete HTML page with the report data embedded."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SENTINEL-X Control Plane</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');
  :root {{
    --bg: #090d16;
    --surface: #0f172a;
    --surface2: #1e293b;
    --surface3: #334155;
    --border: #1e293b;
    --border-subtle: #334155;
    --text: #f8fafc;
    --text-dim: #94a3b8;
    --accent: #38bdf8;
    --accent-glow: rgba(56, 189, 248, 0.15);
    --green: #10b981;
    --green-dim: rgba(16, 185, 129, 0.12);
    --red: #ef4444;
    --red-dim: rgba(239, 68, 68, 0.12);
    --yellow: #f59e0b;
    --yellow-dim: rgba(245, 158, 11, 0.12);
    --purple: #a855f7;
    --purple-dim: rgba(168, 85, 247, 0.12);
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
  }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 32px 24px; }}

  /* Top Nav */
  .navbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    padding-bottom: 20px;
    margin-bottom: 28px;
  }}
  .logo {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .logo h1 {{
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 4px;
    color: var(--text);
    text-transform: uppercase;
  }}
  .logo .badge {{
    background: linear-gradient(135deg, #0284c7, #38bdf8);
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    letter-spacing: 1px;
  }}
  .tagline {{
    font-size: 13px;
    color: var(--text-dim);
  }}

  /* Meta Bar */
  .meta-bar {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 24px;
  }}
  .meta-item {{ display: flex; flex-direction: column; }}
  .meta-label {{ font-size: 11px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-bottom: 4px; }}
  .meta-value {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}

  /* Verdict Card */
  .verdict-banner {{
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 28px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border: 1px solid transparent;
  }}
  .verdict-VERIFIED {{ background: var(--green-dim); border-color: rgba(16, 185, 129, 0.4); }}
  .verdict-BLOCKED {{ background: var(--red-dim); border-color: rgba(239, 68, 68, 0.4); }}
  .verdict-REVIEW {{ background: var(--yellow-dim); border-color: rgba(245, 158, 11, 0.4); }}
  .verdict-INCOMPLETE {{ background: var(--surface2); border-color: var(--border-subtle); }}

  .verdict-left h2 {{ font-size: 28px; font-weight: 900; letter-spacing: 2px; }}
  .verdict-left p {{ font-size: 14px; margin-top: 4px; opacity: 0.85; }}
  .verdict-VERIFIED .verdict-left h2 {{ color: var(--green); }}
  .verdict-BLOCKED .verdict-left h2 {{ color: var(--red); }}
  .verdict-REVIEW .verdict-left h2 {{ color: var(--yellow); }}
  .verdict-INCOMPLETE .verdict-left h2 {{ color: var(--text-dim); }}

  /* Tabs */
  .tabs {{
    display: flex;
    gap: 8px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
  }}
  .tab-btn {{
    background: transparent;
    border: none;
    color: var(--text-dim);
    font-family: inherit;
    font-size: 13px;
    font-weight: 600;
    padding: 10px 18px;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
  }}
  .tab-btn:hover {{ color: var(--text); }}
  .tab-btn.active {{
    color: var(--accent);
    border-bottom-color: var(--accent);
  }}

  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}

  /* Cards & Sections */
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
  }}
  .card-title {{
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  /* Grid for checks */
  .checks-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 12px;
  }}
  .check-item {{
    background: var(--surface2);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 12px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .check-name {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; }}
  .badge-pass {{ background: var(--green-dim); color: var(--green); padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }}
  .badge-fail {{ background: var(--red-dim); color: var(--red); padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }}
  .badge-dim {{ background: var(--surface3); color: var(--text-dim); padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }}

  /* Findings */
  .finding {{
    background: var(--surface2);
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 12px;
    border-left: 4px solid var(--border-subtle);
  }}
  .finding-confirmed {{ border-left-color: var(--red); }}
  .finding-unconfirmed {{ border-left-color: var(--yellow); }}
  .finding-header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }}
  .finding-title {{ font-size: 14px; font-weight: 700; color: var(--text); }}
  .finding-meta {{ font-size: 11px; color: var(--text-dim); font-family: 'JetBrains Mono', monospace; }}
  .finding-desc {{ font-size: 13px; color: var(--text-dim); margin-bottom: 8px; }}
  .finding-rec {{ font-size: 12px; background: rgba(0,0,0,0.2); padding: 6px 10px; border-radius: 4px; color: #cbd5e1; }}

  /* Timeline & Spans */
  .timeline {{
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .timeline-event {{
    background: var(--surface2);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 12px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .event-left {{ display: flex; align-items: center; gap: 12px; }}
  .event-icon {{ font-size: 14px; width: 24px; text-align: center; }}
  .event-title {{ font-size: 13px; font-weight: 600; }}
  .event-type {{ font-size: 11px; color: var(--text-dim); text-transform: uppercase; font-family: 'JetBrains Mono', monospace; }}
  .event-right {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--text-dim); }}

  /* Table */
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; padding: 10px 12px; color: var(--text-dim); font-size: 11px; text-transform: uppercase; border-bottom: 1px solid var(--border); }}
  td {{ padding: 12px; border-bottom: 1px solid var(--border); }}
  tr:last-child td {{ border-bottom: none; }}

  /* Metrics Summary */
  .metrics-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 20px;
  }}
  .metric-box {{
    background: var(--surface2);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 16px;
  }}
  .metric-val {{ font-size: 24px; font-weight: 800; font-family: 'JetBrains Mono', monospace; color: var(--accent); margin-top: 4px; }}

  /* Diff block */
  pre.diff {{
    background: #020617;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    overflow-x: auto;
    color: #94a3b8;
    line-height: 1.5;
  }}
</style>
</head>
<body>

<div class="container">
  <div class="navbar">
    <div class="logo">
      <h1>Sentinel<span style="color:var(--accent);">-X</span></h1>
      <span class="badge">CONTROL PLANE</span>
    </div>
    <div class="tagline">AI Agent Reliability, Security & Verification</div>
  </div>

  <div id="app"></div>
</div>

<script>
const report = {report_json_str};

function renderApp() {{
  const app = document.getElementById("app");
  const verdict = report.verdict || "UNKNOWN";

  let verdictDesc = "";
  if (verdict === "VERIFIED") verdictDesc = "All deterministic security checks passed & AI critic raised no concerns.";
  else if (verdict === "BLOCKED") verdictDesc = "Critical security issues, failing tests, or blocked tools were detected.";
  else if (verdict === "REVIEW") verdictDesc = "Unconfirmed AI concerns or non-critical findings require human review.";
  else verdictDesc = "Verification could not complete due to missing tools or runtime errors.";

  const confirmed = report.confirmed_findings || [];
  const unconfirmed = report.unconfirmed_findings || [];
  const checks = report.checks || [];
  const decisions = report.tool_decisions || [];
  const executions = report.tool_executions || [];
  const evalReport = report.eval_report || null;
  const metrics = report.metrics || null;
  const events = report.events || [];
  const diffText = report.metadata?.diff_text || "";

  app.innerHTML = `
    <div class="meta-bar">
      <div class="meta-item">
        <span class="meta-label">Run ID</span>
        <span class="meta-value" style="color:var(--accent)">${{report.run_id || "run_local"}}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">Repository</span>
        <span class="meta-value">${{report.repository || "local-repo"}}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">Branch</span>
        <span class="meta-value">${{report.branch || "main"}}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">Commit</span>
        <span class="meta-value">${{report.commit ? report.commit.substring(0, 8) : "unknown"}}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">Timestamp</span>
        <span class="meta-value">${{report.timestamp || "just now"}}</span>
      </div>
    </div>

    <div class="verdict-banner verdict-${{verdict}}">
      <div class="verdict-left">
        <h2>${{verdict}}</h2>
        <p>${{verdictDesc}}</p>
      </div>
      <div class="verdict-right">
        <span style="font-family:'JetBrains Mono'; font-size:12px; opacity:0.8;">CONFIRMED: <b>${{confirmed.length}}</b> · UNCONFIRMED: <b>${{unconfirmed.length}}</b></span>
      </div>
    </div>

    <div class="tabs">
      <button class="tab-btn active" onclick="switchTab('overview')">Overview</button>
      <button class="tab-btn" onclick="switchTab('timeline')">Agent Timeline (${{events.length}})</button>
      <button class="tab-btn" onclick="switchTab('shield')">ToolShield Security (${{decisions.length}})</button>
      <button class="tab-btn" onclick="switchTab('eval')">Evaluation & Red Team</button>
      <button class="tab-btn" onclick="switchTab('telemetry')">Cost & Latency</button>
      <button class="tab-btn" onclick="switchTab('diff')">Git Changes</button>
    </div>

    <!-- OVERVIEW TAB -->
    <div id="tab-overview" class="tab-content active">
      <div class="card">
        <div class="card-title">🛡 Deterministic Checks</div>
        <div class="checks-grid">
          ${{checks.map(c => `
            <div class="check-item">
              <span class="check-name">${{c.name}}</span>
              <span class="badge-${{c.status === 'PASSED' ? 'pass' : c.status === 'FAILED' ? 'fail' : 'dim'}}">${{c.status}}</span>
            </div>
          `).join("") || '<p style="color:var(--text-dim);font-size:13px">No deterministic checks executed.</p>'}
        </div>
      </div>

      <div class="card">
        <div class="card-title">🚨 Confirmed Findings (Deterministic Proof)</div>
        ${{confirmed.length === 0 ? '<p style="color:var(--text-dim);font-size:13px">No confirmed findings. Deterministic checks passed.</p>' : confirmed.map(f => `
          <div class="finding finding-confirmed">
            <div class="finding-header">
              <span class="finding-title">${{f.title}}</span>
              <span class="finding-meta">${{f.source}} · ${{f.file ? f.file + ':' + (f.line || '') : ''}}</span>
            </div>
            <div class="finding-desc">${{f.description}}</div>
            ${{f.recommendation ? `<div class="finding-rec"><b>Fix:</b> ${{f.recommendation}}</div>` : ''}}
          </div>
        `).join("")}}
      </div>

      <div class="card">
        <div class="card-title">💡 Unconfirmed AI Critic Findings (Hypotheses)</div>
        ${{unconfirmed.length === 0 ? '<p style="color:var(--text-dim);font-size:13px">No AI concerns raised.</p>' : unconfirmed.map(f => `
          <div class="finding finding-unconfirmed">
            <div class="finding-header">
              <span class="finding-title">${{f.title}}</span>
              <span class="finding-meta">AI Critic (Gemini) · ${{f.file ? f.file + ':' + (f.line || '') : ''}}</span>
            </div>
            <div class="finding-desc">${{f.description}}</div>
            ${{f.recommendation ? `<div class="finding-rec"><b>Recommendation:</b> ${{f.recommendation}}</div>` : ''}}
          </div>
        `).join("")}}
      </div>
    </div>

    <!-- TIMELINE TAB -->
    <div id="tab-timeline" class="tab-content">
      <div class="card">
        <div class="card-title">⏱ Unified Event Trace Waterfall</div>
        <div class="timeline">
          ${{events.map(e => `
            <div class="timeline-event">
              <div class="event-left">
                <span class="event-icon">${{e.status === 'success' ? '🟢' : e.status === 'blocked' ? '🔴' : '🟡'}}</span>
                <div>
                  <div class="event-title">${{e.component}}</div>
                  <div class="event-type">${{e.event_type}} · ID: ${{e.event_id}}</div>
                </div>
              </div>
              <div class="event-right">
                ${{e.duration_ms ? `${{e.duration_ms}}ms` : ''}}
                ${{e.estimated_cost_usd ? ` · $${{e.estimated_cost_usd.toFixed(6)}}` : ''}}
              </div>
            </div>
          `).join("") || '<p style="color:var(--text-dim);font-size:13px">No events logged in trace.</p>'}
        </div>
      </div>
    </div>

    <!-- TOOLSHIELD TAB -->
    <div id="tab-shield" class="tab-content">
      <div class="card">
        <div class="card-title">🔒 ToolShield Policy Decisions</div>
        <table>
          <thead>
            <tr><th>Tool Name</th><th>Decision</th><th>Risk</th><th>Reason</th><th>Rule ID</th></tr>
          </thead>
          <tbody>
            ${{decisions.map(d => `
              <tr>
                <td style="font-family:'JetBrains Mono';font-weight:600">${{d.tool}}</td>
                <td><span class="badge-${{d.decision === 'ALLOW' ? 'pass' : d.decision === 'DENY' ? 'fail' : 'dim'}}">${{d.decision}}</span></td>
                <td>${{d.risk}}</td>
                <td style="font-family:'JetBrains Mono';font-size:12px">${{d.reason}}</td>
                <td style="color:var(--text-dim);font-size:11px">${{d.rule_id || '-'}}</td>
              </tr>
            `).join("") || '<tr><td colspan="5" style="color:var(--text-dim)">No tool calls evaluated in this run.</td></tr>'}
          </tbody>
        </table>
      </div>
    </div>

    <!-- EVALUATION TAB -->
    <div id="tab-eval" class="tab-content">
      <div class="card">
        <div class="card-title">📊 Evaluation & Red Team Scorecard</div>
        ${{evalReport ? `
          <div class="metrics-grid">
            <div class="metric-box">
              <div class="meta-label">Task Success Rate</div>
              <div class="metric-val" style="color:var(--green)">${{(evalReport.task_success_rate * 100).toFixed(1)}}%</div>
            </div>
            <div class="metric-box">
              <div class="meta-label">Passed Cases</div>
              <div class="metric-val">${{evalReport.passed}} / ${{evalReport.total_cases}}</div>
            </div>
            <div class="metric-box">
              <div class="meta-label">Total Duration</div>
              <div class="metric-val" style="color:var(--accent)">${{evalReport.total_duration_ms.toFixed(0)}}ms</div>
            </div>
          </div>
          <table>
            <thead><tr><th>Case ID</th><th>Name</th><th>Category</th><th>Decision</th><th>Result</th></tr></thead>
            <tbody>
              ${{(evalReport.case_results || []).map(c => `
                <tr>
                  <td style="font-family:'JetBrains Mono'">${{c.case_id}}</td>
                  <td>${{c.name}}</td>
                  <td><span style="color:var(--purple)">${{c.category}}</span></td>
                  <td>${{c.actual_decision || '-'}}</td>
                  <td><span class="badge-${{c.passed ? 'pass' : 'fail'}}">${{c.passed ? 'PASS' : 'FAIL'}}</span></td>
                </tr>
              `).join("")}}
            </tbody>
          </table>
        ` : '<p style="color:var(--text-dim);font-size:13px">Run <code>sentinel verify --eval</code> or <code>sentinel redteam</code> to include evaluation telemetry.</p>'}
      </div>
    </div>

    <!-- TELEMETRY TAB -->
    <div id="tab-telemetry" class="tab-content">
      <div class="card">
        <div class="card-title">⚡ Cost, Tokens & Latency Telemetry</div>
        ${{metrics ? `
          <div class="metrics-grid">
            <div class="metric-box">
              <div class="meta-label">Estimated Cost</div>
              <div class="metric-val" style="color:var(--green)">$${{metrics.estimated_cost_usd.toFixed(6)}}</div>
              <small style="color:var(--text-dim);font-size:10px">ESTIMATED RATE</small>
            </div>
            <div class="metric-box">
              <div class="meta-label">Total Tokens</div>
              <div class="metric-val">${{metrics.total_tokens}}</div>
              <small style="color:var(--text-dim);font-size:10px">${{metrics.input_tokens}} in / ${{metrics.output_tokens}} out</small>
            </div>
            <div class="metric-box">
              <div class="meta-label">LLM Latency</div>
              <div class="metric-val" style="color:var(--accent)">${{metrics.latency_ms.toFixed(0)}}ms</div>
              <small style="color:var(--text-dim);font-size:10px">${{metrics.model}} (${{metrics.provider}})</small>
            </div>
          </div>
        ` : '<p style="color:var(--text-dim);font-size:13px">No LLM calls recorded in this verification run.</p>'}
      </div>
    </div>

    <!-- GIT DIFF TAB -->
    <div id="tab-diff" class="tab-content">
      <div class="card">
        <div class="card-title">📝 Git Unified Diff</div>
        <pre class="diff">${{escapeHtml(diffText || 'No diff text available.')}}</pre>
      </div>
    </div>
  `;
}}

function switchTab(tabId) {{
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('tab-' + tabId).classList.add('active');
}}

function escapeHtml(str) {{
  return (str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}}

renderApp();
</script>
</body>
</html>
"""
