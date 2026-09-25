import os
from pathlib import Path
from sentinel.models import VerificationReport


def generate_markdown_report(report: VerificationReport, output_path: str = ".sentinel/report.md"):
    """Generates the comprehensive Markdown report from the VerificationReport object."""
    os.makedirs(Path(output_path).parent, exist_ok=True)

    lines = [
        "# SENTINEL-X Verification & Reliability Report\n",
        f"**Verdict: {report.verdict.value}**\n",
        f"- Run ID: `{report.run_id or 'run_local'}`",
        f"- Repository: {report.repository}",
        f"- Branch: {report.branch}",
        f"- Commit: {report.commit}",
        f"- Timestamp: {report.timestamp}",
        f"- AI Provider: {report.ai_provider or 'none'}\n",
    ]

    if report.task_description:
        lines.append(f"## Task Description\n\n{report.task_description}\n")

    # Code Change Summary
    lines.append("## Code Changes\n")
    lines.append(f"- Files changed: {len(report.changed_files)}")
    for f in report.changed_files:
        lines.append(f"  - `{f}`")
    lines.append("")

    # Deterministic Checks
    lines.append("## Deterministic Checks\n")
    for check in report.checks:
        icon = "PASS" if check.status.value == "PASSED" else check.status.value
        lines.append(f"### {check.name}")
        lines.append(f"- Status: **{icon}**")
        lines.append(f"- Duration: {check.duration:.2f}s")
        if check.findings:
            lines.append(f"- Findings: {len(check.findings)}")
        lines.append("")

    # Confirmed Findings
    lines.append("## Confirmed Findings (Deterministic)\n")
    if not report.confirmed_findings:
        lines.append("No confirmed findings.\n")
    else:
        for f in report.confirmed_findings:
            lines.append(f"### {f.title}")
            lines.append(f"- **Severity**: {f.severity}")
            lines.append(f"- **Source**: {f.source}")
            if f.file:
                lines.append(f"- **Location**: `{f.file}:{f.line or ''}`")
            lines.append(f"- **Description**: {f.description}")
            if f.recommendation:
                lines.append(f"- **Recommendation**: {f.recommendation}")
            lines.append("")

    # Unconfirmed AI Findings
    lines.append("## Unconfirmed Findings (AI Critic)\n")
    if not report.unconfirmed_findings:
        lines.append("No unconfirmed findings.\n")
    else:
        for f in report.unconfirmed_findings:
            lines.append(f"### {f.title}")
            lines.append(f"- **Severity**: {f.severity}")
            if f.file:
                lines.append(f"- **Location**: `{f.file}:{f.line or ''}`")
            lines.append(f"- **Description**: {f.description}")
            if f.evidence:
                lines.append(f"- **Reasoning**: {f.evidence}")
            if f.recommendation:
                lines.append(f"- **Recommendation**: {f.recommendation}")
            lines.append("")

    # ToolShield Policy Decisions
    if report.tool_decisions:
        lines.append("## ToolShield Policy Decisions\n")
        for dec in report.tool_decisions:
            dec_val = dec.get("decision", "ALLOW")
            lines.append(f"- **Tool `{dec.get('tool', 'unknown')}`**: **{dec_val}** (Reason: `{dec.get('reason', '')}`, Risk: `{dec.get('risk', '')}`)")
        lines.append("")

    # Agent Reliability & Executions
    if report.tool_executions:
        lines.append("## Agent Executions & Reliability\n")
        for ex in report.tool_executions:
            lines.append(f"- **Execution `{ex.get('execution_id', '')}`** (`{ex.get('tool_name', '')}`): Status: **{ex.get('status', '')}**, Retries: {ex.get('retry_count', 0)}, Cached: {ex.get('cached', False)}")
        lines.append("")

    # Evaluation & Red Team Summary
    if report.eval_report:
        ev = report.eval_report
        lines.append("## Deterministic Evaluation & Red Team Suite\n")
        lines.append(f"- Suite: **{ev.get('suite_name', 'Default Suite')}**")
        lines.append(f"- Success Rate: **{ev.get('task_success_rate', 0.0) * 100:.1f}%** ({ev.get('passed', 0)}/{ev.get('total_cases', 0)} passed)")
        dim_scores = ev.get("dimension_scores", {})
        if dim_scores:
            lines.append("- Dimension Breakdown:")
            for dim, score in dim_scores.items():
                lines.append(f"  - `{dim}`: {score * 100:.1f}%")
        lines.append("")

    # Cost & Latency Telemetry
    if report.metrics:
        m = report.metrics
        lines.append("## Cost & Latency Telemetry\n")
        lines.append(f"- Model: `{m.get('model', 'gemini-2.5-flash')}` ({m.get('provider', 'gemini')})")
        lines.append(f"- Tokens: {m.get('input_tokens', 0)} in / {m.get('output_tokens', 0)} out (Total: {m.get('total_tokens', 0)})")
        lines.append(f"- Latency: {m.get('latency_ms', 0.0):.1f}ms")
        lines.append(f"- Estimated Cost: **${m.get('estimated_cost_usd', 0.0):.6f} USD** (Estimated)")
        lines.append("")

    ai_summary = report.ai_review.get("summary", "")
    if ai_summary:
        lines.append("## AI Review Summary\n")
        lines.append(f"{ai_summary}\n")

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
