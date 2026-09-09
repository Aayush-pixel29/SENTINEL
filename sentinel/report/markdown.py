import os
from pathlib import Path
from sentinel.models import VerificationReport, Classification

def generate_markdown_report(report: VerificationReport, output_path: str = ".sentinel/report.md"):
    """Generates the Markdown report from the VerificationReport object."""
    
    os.makedirs(Path(output_path).parent, exist_ok=True)
    
    lines = [
        "# Sentinel Verification Report\n",
        f"## Verdict\n\n**{report.verdict.value}**\n",
        "## Change Summary\n",
        f"- Files changed: {len(report.changed_files)}",
        f"- Commit: {report.commit}\n",
        "## Deterministic Checks\n"
    ]
    
    for check in report.checks:
        lines.append(f"### {check.name.capitalize()}")
        lines.append(f"- Status: {check.status.value}")
        lines.append(f"- Duration: {check.duration:.2f}s")
        lines.append(f"- Findings: {len(check.findings)}\n")
        
    lines.append("## Confirmed Findings\n")
    if not report.confirmed_findings:
        lines.append("No confirmed findings.\n")
    else:
        for f in report.confirmed_findings:
            lines.append(f"### 🔴 {f.title}")
            lines.append(f"- **Severity**: {f.severity}")
            lines.append(f"- **Source**: {f.source}")
            if f.file:
                lines.append(f"- **File**: {f.file}:{f.line if f.line else ''}")
            lines.append(f"- **Description**: {f.description}")
            lines.append("")

    lines.append("## Unconfirmed Findings (AI)\n")
    if not report.unconfirmed_findings:
        lines.append("No unconfirmed findings.\n")
    else:
        for f in report.unconfirmed_findings:
            lines.append(f"### 🟡 {f.title}")
            lines.append(f"- **Severity**: {f.severity}")
            if f.file:
                lines.append(f"- **File**: {f.file}:{f.line if f.line else ''}")
            lines.append(f"- **Description**: {f.description}")
            if f.recommendation:
                lines.append(f"- **Recommendation**: {f.recommendation}")
            lines.append("")
            
    lines.append("## AI Review Summary\n")
    lines.append(report.ai_review.get("summary", "No AI review summary available.\n"))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
