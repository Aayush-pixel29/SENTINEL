from typing import List
from sentinel.models import CheckResult, CheckStatus, Finding, Verdict, AIReviewResult

def determine_verdict(
    checks: List[CheckResult], 
    confirmed_findings: List[Finding], 
    unconfirmed_findings: List[Finding],
    ai_status: CheckStatus
) -> Verdict:
    """
    Determines the final verdict based on priority:
    BLOCKED -> INCOMPLETE -> REVIEW -> VERIFIED
    """
    
    # 1. Check for BLOCKED
    # Failed tests or blocked by deterministic findings
    for check in checks:
        if check.name == "pytest" and check.status == CheckStatus.FAILED:
            return Verdict.BLOCKED

    for finding in confirmed_findings:
        if finding.severity.upper() in ["CRITICAL", "HIGH", "ERROR"]:
            return Verdict.BLOCKED

    # 2. Check for INCOMPLETE
    # Missing tools or errors running tools
    for check in checks:
        if check.status in [CheckStatus.NOT_AVAILABLE, CheckStatus.ERROR]:
            return Verdict.INCOMPLETE
    
    if ai_status in [CheckStatus.NOT_AVAILABLE, CheckStatus.ERROR]:
        return Verdict.INCOMPLETE

    # 3. Check for REVIEW
    # AI generated unconfirmed findings or minor confirmed findings
    if len(unconfirmed_findings) > 0:
        return Verdict.REVIEW
        
    if len(confirmed_findings) > 0:
        return Verdict.REVIEW

    # 4. VERIFIED
    # No findings, everything ran successfully
    return Verdict.VERIFIED
