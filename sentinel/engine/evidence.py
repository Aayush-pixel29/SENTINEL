from typing import List, Dict, Any
from sentinel.models import CheckResult, Finding, Classification, AIReviewResult, GitChangeSummary

def get_confirmed_findings(checks: List[CheckResult]) -> List[Finding]:
    """Extracts all CONFIRMED findings from the check results."""
    confirmed = []
    for check in checks:
        for finding in check.findings:
            if finding.classification == Classification.CONFIRMED:
                confirmed.append(finding)
    return confirmed

def get_unconfirmed_findings(ai_review: AIReviewResult) -> List[Finding]:
    """Extracts UNCONFIRMED findings from AI review."""
    return [
        f for f in ai_review.findings 
        if f.classification == Classification.UNCONFIRMED
    ]

def gather_evidence_context(
    diff: GitChangeSummary,
    checks: List[CheckResult],
    task_description: str
) -> str:
    """Formats the context to be sent to the AI critic."""
    
    context = f"TASK\n{task_description}\n\n"
    context += f"CHANGE\n{diff.diff_text}\n\n"
    
    context += "DETERMINISTIC RESULTS\n"
    for check in checks:
        context += f"\n--- {check.name.upper()} ---\n"
        context += f"Status: {check.status.value}\n"
        context += f"Findings: {len(check.findings)}\n"
        if check.findings:
            for f in check.findings:
                context += f"- [{f.severity}] {f.title}: {f.description}\n"
    
    return context
