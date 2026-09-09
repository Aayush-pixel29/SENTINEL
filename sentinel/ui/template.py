"""Builds a self-contained HTML dashboard from report JSON."""


def build_html(report_json_str: str) -> str:
    """Return a complete HTML page with the report data embedded."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sentinel - Verification Dashboard</title>
<style>
  :root {{
    --bg: #0d1117;
    --surface: #161b22;
    --surface2: #1c2333;
    --border: #30363d;
    --text: #e6edf3;
    --text-dim: #8b949e;
    --accent: #58a6ff;
    --green: #3fb950;
    --red: #f85149;
    --yellow: #d29922;
    --orange: #db6d28;
    --purple: #bc8cff;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
  }}
  .container {{ max-width: 960px; margin: 0 auto; padding: 24px 20px; }}

  /* Header */
  .header {{
    text-align: center;
    padding: 32px 0 24px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 32px;
  }}
  .header h1 {{
    font-size: 28px;
    font-weight: 700;
    letter-spacing: 6px;
    color: var(--accent);
    margin-bottom: 6px;
  }}
  .header .subtitle {{
    color: var(--text-dim);
    font-size: 14px;
  }}

  /* Meta bar */
  .meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    padding: 16px 20px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 24px;
    font-size: 14px;
  }}
  .meta-item {{ display: flex; flex-direction: column; }}
  .meta-label {{ color: var(--text-dim); font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }}
  .meta-value {{ color: var(--text); font-weight: 600; font-family: 'SF Mono', 'Consolas', monospace; }}

  /* Verdict card */
  .verdict-card {{
    text-align: center;
    padding: 32px;
    border-radius: 12px;
    margin-bottom: 32px;
    border: 2px solid var(--border);
  }}
  .verdict-card.BLOCKED {{ border-color: var(--red); background: rgba(248,81,73,0.08); }}
  .verdict-card.REVIEW {{ border-color: var(--yellow); background: rgba(210,153,34,0.08); }}
  .verdict-card.VERIFIED {{ border-color: var(--green); background: rgba(63,185,80,0.08); }}
  .verdict-card.INCOMPLETE {{ border-color: var(--text-dim); background: rgba(139,148,158,0.08); }}
  .verdict-label {{ font-size: 42px; font-weight: 800; letter-spacing: 4px; }}
  .verdict-card.BLOCKED .verdict-label {{ color: var(--red); }}
  .verdict-card.REVIEW .verdict-label {{ color: var(--yellow); }}
  .verdict-card.VERIFIED .verdict-label {{ color: var(--green); }}
  .verdict-card.INCOMPLETE .verdict-label {{ color: var(--text-dim); }}
  .verdict-summary {{ color: var(--text-dim); margin-top: 8px; font-size: 14px; }}

  /* Section */
  .section {{
    margin-bottom: 28px;
  }}
  .section-title {{
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--text-dim);
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }}

  /* Checks grid */
  .checks-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 10px;
  }}
  .check-item {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 14px;
  }}
  .check-name {{ font-weight: 600; }}
  .check-status {{ font-weight: 700; font-size: 12px; padding: 3px 10px; border-radius: 12px; }}
  .check-status.PASSED {{ color: var(--green); background: rgba(63,185,80,0.12); }}
  .check-status.FAILED {{ color: var(--red); background: rgba(248,81,73,0.12); }}
  .check-status.NOT_AVAILABLE {{ color: var(--text-dim); background: rgba(139,148,158,0.1); }}
  .check-status.ERROR {{ color: var(--orange); background: rgba(219,109,40,0.12); }}

  /* Finding card */
  .finding {{
    padding: 16px 20px;
    background: var(--surface);
    border-left: 4px solid var(--border);
    border-radius: 0 8px 8px 0;
    margin-bottom: 12px;
  }}
  .finding.confirmed {{ border-left-color: var(--red); }}
  .finding.unconfirmed {{ border-left-color: var(--yellow); }}
  .finding-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
  .finding-title {{ font-weight: 700; font-size: 15px; }}
  .finding.confirmed .finding-title {{ color: var(--red); }}
  .finding.unconfirmed .finding-title {{ color: var(--yellow); }}
  .finding-badge {{
    font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 10px;
    text-transform: uppercase; letter-spacing: 1px;
  }}
  .finding-badge.CONFIRMED {{ background: rgba(248,81,73,0.15); color: var(--red); }}
  .finding-badge.UNCONFIRMED {{ background: rgba(210,153,34,0.15); color: var(--yellow); }}
  .finding-meta {{ font-size: 13px; color: var(--text-dim); margin-bottom: 8px; }}
  .finding-desc {{ font-size: 14px; color: var(--text); }}
  .finding-rec {{ font-size: 13px; color: var(--accent); margin-top: 8px; }}
  .finding-evidence {{ font-size: 13px; color: var(--text-dim); margin-top: 6px; font-style: italic; }}

  /* Change summary */
  .change-files {{ list-style: none; padding: 0; }}
  .change-files li {{
    padding: 6px 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    margin-bottom: 4px;
    font-family: 'SF Mono', 'Consolas', monospace;
    font-size: 13px;
  }}

  /* AI review */
  .ai-summary {{
    padding: 16px 20px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 14px;
    color: var(--text);
  }}

  /* Footer */
  .footer {{
    text-align: center;
    padding: 24px 0;
    margin-top: 32px;
    border-top: 1px solid var(--border);
    color: var(--text-dim);
    font-size: 12px;
  }}
  .footer a {{ color: var(--accent); text-decoration: none; }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>SENTINEL</h1>
  <div class="subtitle">Evidence-driven verification for AI-generated code</div>
</div>

<div id="app"></div>

<div class="footer">
  Sentinel v1.0 &mdash; AI writes the code. Sentinel verifies what can actually be verified.
</div>

</div>

<script>
const report = {report_json_str};

function render() {{
  const app = document.getElementById('app');
  const v = report.verdict;
  const summaryMap = {{
    'BLOCKED':    'This change should not be merged yet.',
    'REVIEW':     'This change requires human review before merging.',
    'VERIFIED':   'All checks passed. This change is ready for review.',
    'INCOMPLETE': 'Verification is incomplete. Some checks could not run.',
  }};

  let html = '';

  // Meta
  html += '<div class="meta">';
  html += meta('Repository', report.repository || 'unknown');
  html += meta('Branch', report.branch || 'unknown');
  html += meta('Commit', report.commit || 'unknown');
  html += meta('Timestamp', report.timestamp || 'unknown');
  html += meta('AI Provider', (report.ai_provider || 'none').charAt(0).toUpperCase() + (report.ai_provider || 'none').slice(1));
  html += '</div>';

  // Verdict
  html += `<div class="verdict-card ${{v}}">`;
  html += `<div class="verdict-label">${{v}}</div>`;
  html += `<div class="verdict-summary">${{summaryMap[v] || ''}}</div>`;
  const nc = (report.confirmed_findings || []).length;
  const nu = (report.unconfirmed_findings || []).length;
  if (nc || nu) {{
    html += `<div class="verdict-summary" style="margin-top:6px">`;
    if (nc) html += `${{nc}} confirmed issue${{nc>1?'s':''}}`;
    if (nc && nu) html += ` &middot; `;
    if (nu) html += `${{nu}} unconfirmed concern${{nu>1?'s':''}}`;
    html += '</div>';
  }}
  html += '</div>';

  // Checks
  html += '<div class="section"><div class="section-title">Verification Evidence</div>';
  html += '<div class="checks-grid">';
  for (const c of (report.checks || [])) {{
    html += `<div class="check-item"><span class="check-name">${{c.name}}</span>`;
    html += `<span class="check-status ${{c.status}}">${{c.status}}</span></div>`;
  }}
  html += '</div></div>';

  // Confirmed
  if (nc) {{
    html += '<div class="section"><div class="section-title">Confirmed Findings</div>';
    for (const f of report.confirmed_findings) {{
      html += findingCard(f, 'confirmed');
    }}
    html += '</div>';
  }}

  // Unconfirmed
  if (nu) {{
    html += '<div class="section"><div class="section-title">Unconfirmed AI Concerns</div>';
    for (const f of report.unconfirmed_findings) {{
      html += findingCard(f, 'unconfirmed');
    }}
    html += '</div>';
  }}

  // AI summary
  const aiSum = report.ai_review && report.ai_review.summary;
  if (aiSum) {{
    html += '<div class="section"><div class="section-title">AI Review Summary</div>';
    html += `<div class="ai-summary">${{escapeHtml(aiSum)}}</div></div>`;
  }}

  // Changed files
  if (report.changed_files && report.changed_files.length) {{
    html += '<div class="section"><div class="section-title">Changed Files</div>';
    html += '<ul class="change-files">';
    for (const f of report.changed_files) {{
      html += `<li>${{escapeHtml(f)}}</li>`;
    }}
    html += '</ul></div>';
  }}

  app.innerHTML = html;
}}

function meta(label, value) {{
  return `<div class="meta-item"><span class="meta-label">${{label}}</span><span class="meta-value">${{escapeHtml(value)}}</span></div>`;
}}

function findingCard(f, cls) {{
  let h = `<div class="finding ${{cls}}">`;
  h += `<div class="finding-header"><span class="finding-title">${{escapeHtml(f.title)}}</span>`;
  h += `<span class="finding-badge ${{f.classification}}">${{f.classification}}</span></div>`;
  const loc = f.file ? (f.file + (f.line ? ':' + f.line : '')) : '';
  if (loc || f.source) {{
    h += `<div class="finding-meta">`;
    if (loc) h += `${{escapeHtml(loc)}}`;
    if (loc && f.source) h += ` &middot; `;
    if (f.source) h += `Detected by ${{escapeHtml(f.source)}}`;
    h += `</div>`;
  }}
  if (f.description) h += `<div class="finding-desc">${{escapeHtml(f.description)}}</div>`;
  if (f.evidence) h += `<div class="finding-evidence">Reasoning: ${{escapeHtml(f.evidence)}}</div>`;
  if (f.recommendation) h += `<div class="finding-rec">Recommendation: ${{escapeHtml(f.recommendation)}}</div>`;
  h += '</div>';
  return h;
}}

function escapeHtml(s) {{
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

render();
</script>
</body>
</html>"""
