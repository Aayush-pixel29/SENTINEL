import os
from pathlib import Path
from sentinel.models import VerificationReport


def generate_markdown_report(report: VerificationReport, output_path: str = ".sentinel/report.md"):
    """Generates the Markdown report from the VerificationReport object."""
    os.makedirs(Path(output_path).parent, exist_ok=True)

    lines = [
        "# Sentinel Verification Report\n",
        f"**Verdict: {report.verdict.value}**\n",
        f"- Repository: {report.repository}",
        f"- Branch: {report.branch}",
        f"- Commit: {report.commit}",
        f"- Timestamp: {report.timestamp}",
        f"- AI Provider: {report.ai_provider or 'none'}\n",
    ]

    if report.task_description:
        lines.append(f"## Task\n\n{report.task_description}\n")

    lines.append("## Change Summary\n")
    lines.append(f"- Files changed: {len(report.changed_files)}")
    for f in report.changed_files:
        lines.append(f"  - `{f}`")
    lines.append("")

    lines.append("## Deterministic Checks\n")
    for check in report.checks:
        icon = "PASS" if check.status.value == "PASSED" else check.status.value
        lines.append(f"### {check.name}")
        lines.append(f"- Status: **{icon}**")
        lines.append(f"- Duration: {check.duration:.2f}s")
        if check.findings:
            lines.append(f"- Findings: {len(check.findings)}")
        lines.append("")

    lines.append("## Confirmed Findings\n")
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

    lines.append("## Unconfirmed Findings (AI)\n")
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

    ai_summary = report.ai_review.get("summary", "")
    if ai_summary:
        lines.append("## AI Review Summary\n")
        lines.append(f"{ai_summary}\n")

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
