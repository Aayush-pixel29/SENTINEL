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
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');
  :root {{
    --bg: #0a0e17;
    --surface: #111827;
    --surface2: #1a2234;
    --surface3: #1f2b3d;
    --border: #2a3548;
    --text: #e8edf5;
    --text-dim: #8896aa;
    --accent: #60a5fa;
    --green: #34d399;
    --green-dim: rgba(52,211,153,0.1);
    --red: #f87171;
    --red-dim: rgba(248,113,113,0.08);
    --yellow: #fbbf24;
    --yellow-dim: rgba(251,191,36,0.08);
    --orange: #fb923c;
    --purple: #a78bfa;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
  }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 24px 20px; }}

  /* Header */
  .header {{
    text-align: center;
    padding: 40px 0 28px;
    margin-bottom: 32px;
  }}
  .header h1 {{
    font-size: 24px;
    font-weight: 800;
    letter-spacing: 8px;
    color: var(--accent);
    margin-bottom: 4px;
    text-transform: uppercase;
  }}
  .header .tagline {{
    color: var(--text-dim);
    font-size: 13px;
    font-weight: 400;
  }}

  /* Meta bar */
  .meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    padding: 14px 20px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    margin-bottom: 24px;
    font-size: 13px;
  }}
  .meta-item {{ display: flex; flex-direction: column; min-width: 100px; }}
  .meta-label {{ color: var(--text-dim); font-size: 10px; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600; }}
  .meta-value {{ color: var(--text); font-weight: 600; font-family: 'JetBrains Mono', monospace; font-size: 13px; }}

  /* Verdict card */
  .verdict-card {{
    text-align: center;
    padding: 36px 28px;
    border-radius: 14px;
    margin-bottom: 28px;
    border: 2px solid var(--border);
    position: relative;
    overflow: hidden;
  }}
  .verdict-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
  }}
  .verdict-card.BLOCKED {{ border-color: var(--red); background: var(--red-dim); }}
  .verdict-card.BLOCKED::before {{ background: var(--red); }}
  .verdict-card.REVIEW {{ border-color: var(--yellow); background: var(--yellow-dim); }}
  .verdict-card.REVIEW::before {{ background: var(--yellow); }}
  .verdict-card.VERIFIED {{ border-color: var(--green); background: var(--green-dim); }}
  .verdict-card.VERIFIED::before {{ background: var(--green); }}
  .verdict-card.INCOMPLETE {{ border-color: var(--text-dim); background: rgba(139,148,158,0.05); }}
  .verdict-card.INCOMPLETE::before {{ background: var(--text-dim); }}
  .verdict-label {{ font-size: 48px; font-weight: 900; letter-spacing: 6px; }}
  .verdict-card.BLOCKED .verdict-label {{ color: var(--red); }}
  .verdict-card.REVIEW .verdict-label {{ color: var(--yellow); }}
  .verdict-card.VERIFIED .verdict-label {{ color: var(--green); }}
  .verdict-card.INCOMPLETE .verdict-label {{ color: var(--text-dim); }}
  .verdict-msg {{ color: var(--text-dim); margin-top: 8px; font-size: 14px; }}
  .verdict-counts {{ color: var(--text-dim); margin-top: 6px; font-size: 13px; }}

  /* Why blocked */
  .why-box {{
    padding: 18px 22px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--red);
    border-radius: 0 10px 10px 0;
    margin-bottom: 28px;
    font-size: 14px;
  }}
  .why-box h3 {{ color: var(--red); font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; font-weight: 700; }}
  .why-item {{ margin-bottom: 6px; color: var(--text); }}
  .why-action {{ margin-top: 12px; color: var(--accent); font-weight: 500; }}

  /* Section */
  .section {{ margin-bottom: 28px; }}
  .section-title {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--text-dim);
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
    font-weight: 700;
  }}

  /* Checks grid */
  .checks-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 8px; }}
  .check-item {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 14px;
    transition: background 0.15s;
  }}
  .check-item:hover {{ background: var(--surface2); }}
  .check-name {{ font-weight: 600; }}
  .check-badge {{ font-size: 11px; font-weight: 700; padding: 2px 10px; border-radius: 10px; letter-spacing: 0.5px; }}
  .check-badge.PASSED {{ color: var(--green); background: rgba(52,211,153,0.12); }}
  .check-badge.FAILED {{ color: var(--red); background: rgba(248,113,113,0.12); }}
  .check-badge.NOT_AVAILABLE {{ color: var(--text-dim); background: rgba(139,148,158,0.08); }}
  .check-badge.ERROR {{ color: var(--orange); background: rgba(251,146,60,0.12); }}

  /* What was checked */
  .checked-list {{ list-style: none; padding: 0; }}
  .checked-list li {{
    padding: 6px 0;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .checked-list .icon {{ font-size: 14px; width: 18px; text-align: center; }}
  .checked-list .pass {{ color: var(--green); }}
  .checked-list .fail {{ color: var(--red); }}
  .checked-list .na {{ color: var(--text-dim); }}
  .checked-list .warn {{ color: var(--yellow); }}
  .not-verified {{ margin-top: 12px; padding: 12px 16px; background: var(--surface2); border-radius: 8px; font-size: 13px; color: var(--text-dim); }}

  /* Finding card */
  .finding {{
    padding: 18px 22px;
    background: var(--surface);
    border-left: 4px solid var(--border);
    border-radius: 0 10px 10px 0;
    margin-bottom: 10px;
    transition: background 0.15s;
  }}
  .finding:hover {{ background: var(--surface2); }}
  .finding.confirmed {{ border-left-color: var(--red); }}
  .finding.unconfirmed {{ border-left-color: var(--yellow); }}
  .finding-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; flex-wrap: wrap; gap: 8px; }}
  .finding-title {{ font-weight: 700; font-size: 15px; }}
  .finding.confirmed .finding-title {{ color: var(--red); }}
  .finding.unconfirmed .finding-title {{ color: var(--yellow); }}
  .badge {{
    font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 10px;
    text-transform: uppercase; letter-spacing: 1px;
  }}
  .badge.CONFIRMED {{ background: rgba(248,113,113,0.15); color: var(--red); }}
  .badge.UNCONFIRMED {{ background: rgba(251,191,36,0.15); color: var(--yellow); }}
  .badge.sev {{ background: rgba(96,165,250,0.12); color: var(--accent); margin-left: 4px; }}
  .finding-meta {{ font-size: 13px; color: var(--text-dim); margin-bottom: 8px; font-family: 'JetBrains Mono', monospace; }}
  .finding-desc {{ font-size: 14px; color: var(--text); line-height: 1.5; }}
  .finding-extra {{ font-size: 13px; margin-top: 8px; line-height: 1.5; }}
  .finding-extra.reasoning {{ color: var(--text-dim); font-style: italic; }}
  .finding-extra.rec {{ color: var(--accent); }}

  /* Diff */
  .diff-block {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 10px;
  }}
  .diff-filename {{
    padding: 8px 16px;
    background: var(--surface2);
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 600;
    color: var(--accent);
    border-bottom: 1px solid var(--border);
  }}
  .diff-content {{
    padding: 0;
    max-height: 300px;
    overflow-y: auto;
  }}
  .diff-content pre {{
    margin: 0;
    padding: 12px 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-all;
  }}

  /* AI summary */
  .ai-summary {{
    padding: 16px 20px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    font-size: 14px;
  }}

  /* Copy / actions */
  .actions {{ display: flex; gap: 10px; margin-bottom: 24px; flex-wrap: wrap; }}
  .btn {{
    padding: 8px 18px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    font-family: inherit;
    transition: all 0.15s;
  }}
  .btn:hover {{ background: var(--surface2); border-color: var(--accent); }}
  .btn.primary {{ background: var(--accent); color: var(--bg); border-color: var(--accent); }}
  .btn.primary:hover {{ opacity: 0.9; }}

  /* Footer */
  .footer {{
    text-align: center;
    padding: 28px 0;
    margin-top: 32px;
    border-top: 1px solid var(--border);
    color: var(--text-dim);
    font-size: 12px;
  }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>Sentinel</h1>
  <div class="tagline">Evidence-driven verification for AI-generated code</div>
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
  const msgMap = {{
    'BLOCKED':    'This change should not be merged yet.',
    'REVIEW':     'This change requires human review before merging.',
    'VERIFIED':   'Required verification checks passed. No significant confirmed findings remain. Human review is still recommended.',
    'INCOMPLETE': 'Verification is incomplete. Some required checks could not run.',
  }};

  let html = '';

  // Meta
  html += '<div class="meta">';
  html += meta('Repository', report.repository || '-');
  html += meta('Branch', report.branch || '-');
  html += meta('Commit', report.commit || '-');
  html += meta('Timestamp', (report.timestamp || '').replace('T',' ').slice(0,19));
  html += meta('AI Provider', cap(report.ai_provider || 'none'));
  html += '</div>';

  // Verdict card
  const nc = (report.confirmed_findings || []).length;
  const nu = (report.unconfirmed_findings || []).length;
  html += `<div class="verdict-card ${{v}}">`;
  html += `<div class="verdict-label">${{v}}</div>`;
  html += `<div class="verdict-msg">${{msgMap[v] || ''}}</div>`;
  if (nc || nu) {{
    let parts = [];
    if (nc) parts.push(`${{nc}} confirmed issue${{nc>1?'s':''}}`);
    if (nu) parts.push(`${{nu}} unconfirmed concern${{nu>1?'s':''}}`);
    html += `<div class="verdict-counts">${{parts.join(' &middot; ')}}</div>`;
  }}
  html += '</div>';

  // Why blocked / Why review
  if (v === 'BLOCKED' || v === 'REVIEW') {{
    html += `<div class="why-box">`;
    html += `<h3>Why ${{v === 'BLOCKED' ? 'blocked' : 'review needed'}}</h3>`;
    let idx = 1;
    for (const f of (report.confirmed_findings || [])) {{
      const loc = f.file ? ` in ${{esc(f.file)}}${{f.line ? ':'+f.line : ''}}` : '';
      html += `<div class="why-item">${{idx++}}. <strong>${{esc(f.source)}}</strong> confirmed a ${{esc(f.severity)}} severity ${{esc(f.title).toLowerCase()}}${{loc}}.</div>`;
    }}
    for (const f of (report.unconfirmed_findings || [])) {{
      const loc = f.file ? ` in ${{esc(f.file)}}${{f.line ? ':'+f.line : ''}}` : '';
      html += `<div class="why-item">${{idx++}}. Gemini identified a possible ${{esc(f.title).toLowerCase()}}${{loc}}. This is <strong>UNCONFIRMED</strong>.</div>`;
    }}
    // Action
    const hasConfirmed = nc > 0;
    if (hasConfirmed) {{
      html += `<div class="why-action">Recommended: Fix confirmed issues, then re-run <code>sentinel verify</code>.</div>`;
    }} else {{
      html += `<div class="why-action">Recommended: Manually verify AI concerns, then decide whether to merge.</div>`;
    }}
    html += '</div>';
  }}

  // Actions
  html += '<div class="actions">';
  html += '<button class="btn primary" onclick="copyMarkdown()">Copy Markdown Report</button>';
  html += '<button class="btn" onclick="copyJSON()">Copy JSON Report</button>';
  html += '</div>';

  // What was actually verified
  html += '<div class="section"><div class="section-title">What was actually verified</div>';
  html += '<ul class="checked-list">';
  for (const c of (report.checks || [])) {{
    let icon, cls, label;
    if (c.status === 'PASSED') {{
      icon = '&#10003;'; cls = 'pass';
      label = c.name === 'pytest' ? `${{c.name}} executed` : `${{c.name}} completed`;
    }} else if (c.status === 'FAILED') {{
      const n = (c.findings || []).length;
      icon = '&#10007;'; cls = 'fail';
      label = `${{c.name}} &mdash; ${{n}} finding${{n!==1?'s':''}}`;
    }} else {{
      icon = '&#9675;'; cls = 'na';
      label = `${{c.name}} &mdash; ${{c.status.replace(/_/g,' ').toLowerCase()}}`;
    }}
    html += `<li><span class="icon ${{cls}}">${{icon}}</span> ${{label}}</li>`;
  }}
  // AI
  const aiSt = report.ai_review ? report.ai_review.status : 'SKIPPED';
  if (aiSt === 'PASSED') {{
    html += `<li><span class="icon pass">&#10003;</span> Gemini reviewed the change</li>`;
  }} else {{
    html += `<li><span class="icon na">&#9675;</span> Gemini &mdash; ${{aiSt.replace(/_/g,' ').toLowerCase()}}</li>`;
  }}
  html += '<li><span class="icon pass">&#10003;</span> Git diff analyzed</li>';
  html += '</ul>';
  html += '<div class="not-verified">';
  html += '<strong style="color:var(--yellow)">Not verified:</strong> Runtime behavior in production &middot; External service behavior &middot; Full exploitability &middot; Business logic correctness';
  html += '</div></div>';

  // Checks grid
  html += '<div class="section"><div class="section-title">Verification Evidence</div>';
  html += '<div class="checks-grid">';
  for (const c of (report.checks || [])) {{
    html += `<div class="check-item"><span class="check-name">${{c.name}}</span>`;
    html += `<span class="check-badge ${{c.status}}">${{c.status.replace(/_/g,' ')}}</span></div>`;
  }}
  html += '</div></div>';

  // Confirmed
  if (nc) {{
    html += '<div class="section"><div class="section-title">Confirmed Findings</div>';
    for (const f of report.confirmed_findings) html += findingCard(f, 'confirmed');
    html += '</div>';
  }}

  // Unconfirmed
  if (nu) {{
    html += '<div class="section"><div class="section-title">Unconfirmed AI Concerns</div>';
    for (const f of report.unconfirmed_findings) html += findingCard(f, 'unconfirmed');
    html += '</div>';
  }}

  // AI summary
  const aiSum = report.ai_review && report.ai_review.summary;
  if (aiSum && aiSum !== 'Disabled') {{
    html += '<div class="section"><div class="section-title">AI Review Summary</div>';
    html += `<div class="ai-summary">${{esc(aiSum)}}</div></div>`;
  }}

  // Diff
  if (report.metadata && report.metadata.diff_text) {{
    html += '<div class="section"><div class="section-title">Changes</div>';
    html += renderDiff(report.metadata.diff_text);
    html += '</div>';
  }}

  // Changed files
  if (report.changed_files && report.changed_files.length) {{
    html += '<div class="section"><div class="section-title">Changed Files</div>';
    for (const f of report.changed_files) {{
      html += `<div class="check-item"><span class="check-name" style="font-family:\'JetBrains Mono\',monospace;font-size:13px">${{esc(f)}}</span></div>`;
    }}
    html += '</div>';
  }}

  app.innerHTML = html;
}}

function meta(label, value) {{
  return `<div class="meta-item"><span class="meta-label">${{label}}</span><span class="meta-value">${{esc(value)}}</span></div>`;
}}

function findingCard(f, cls) {{
  let h = `<div class="finding ${{cls}}">`;
  h += `<div class="finding-header"><span class="finding-title">${{esc(f.title)}}</span><span>`;
  h += `<span class="badge ${{f.classification}}">${{f.classification}}</span>`;
  if (f.severity) h += `<span class="badge sev">${{f.severity}}</span>`;
  h += `</span></div>`;
  const loc = f.file ? (f.file + (f.line ? ':' + f.line : '')) : '';
  if (loc || f.source) {{
    h += `<div class="finding-meta">`;
    if (loc) h += esc(loc);
    if (loc && f.source) h += ` &middot; `;
    if (f.source) h += `Detected by ${{esc(f.source)}}`;
    h += `</div>`;
  }}
  if (f.description) h += `<div class="finding-desc">${{esc(f.description)}}</div>`;
  if (f.evidence) h += `<div class="finding-extra reasoning">Reasoning: ${{esc(f.evidence)}}</div>`;
  if (f.recommendation) h += `<div class="finding-extra rec">Recommendation: ${{esc(f.recommendation)}}</div>`;
  h += '</div>';
  return h;
}}

function renderDiff(text) {{
  if (!text) return '';
  const lines = text.split('\\n');
  let html = '';
  let currentFile = '';
  let buffer = [];

  function flush() {{
    if (currentFile && buffer.length) {{
      html += `<div class="diff-block"><div class="diff-filename">${{esc(currentFile)}}</div>`;
      html += `<div class="diff-content"><pre>${{buffer.join('\\n')}}</pre></div></div>`;
    }}
    buffer = [];
  }}

  for (const line of lines) {{
    if (line.startsWith('diff --git')) {{
      flush();
      const m = line.match(/b\\/(.+)$/);
      currentFile = m ? m[1] : 'unknown';
    }} else if (line.startsWith('@@')) {{
      buffer.push(`<span style="color:var(--purple)">${{esc(line)}}</span>`);
    }} else if (line.startsWith('+') && !line.startsWith('+++')) {{
      buffer.push(`<span style="color:var(--green)">${{esc(line)}}</span>`);
    }} else if (line.startsWith('-') && !line.startsWith('---')) {{
      buffer.push(`<span style="color:var(--red)">${{esc(line)}}</span>`);
    }} else if (!line.startsWith('---') && !line.startsWith('+++') && !line.startsWith('index')) {{
      buffer.push(esc(line));
    }}
  }}
  flush();
  return html;
}}

function copyMarkdown() {{
  fetch('/report.md').then(r => r.text()).then(t => {{
    navigator.clipboard.writeText(t).then(() => alert('Markdown report copied to clipboard.'));
  }}).catch(() => {{
    // fallback: copy JSON
    navigator.clipboard.writeText(JSON.stringify(report, null, 2)).then(() => alert('JSON report copied to clipboard.'));
  }});
}}

function copyJSON() {{
  navigator.clipboard.writeText(JSON.stringify(report, null, 2)).then(() => alert('JSON report copied to clipboard.'));
}}

function esc(s) {{
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

function cap(s) {{ return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''; }}

render();
</script>
</body>
</html>"""
