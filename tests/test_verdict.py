from sentinel.engine.verdict import determine_verdict
from sentinel.models import CheckResult, CheckStatus, Finding, Verdict, Classification

def test_verdict_blocked_by_critical_finding():
    finding = Finding(
        id="1", source="semgrep", classification=Classification.CONFIRMED,
        severity="CRITICAL", title="SQLi", description=""
    )
    v = determine_verdict([], [finding], [], CheckStatus.PASSED)
    assert v == Verdict.BLOCKED

def test_verdict_review_for_unconfirmed():
    finding = Finding(
        id="2", source="ai", classification=Classification.UNCONFIRMED,
        severity="MEDIUM", title="Auth", description=""
    )
    v = determine_verdict([], [], [finding], CheckStatus.PASSED)
    assert v == Verdict.REVIEW

def test_verdict_incomplete_for_missing_tool():
    check = CheckResult(
        name="pytest", status=CheckStatus.NOT_AVAILABLE,
        exit_code=-1, duration=0, stdout="", stderr=""
    )
    v = determine_verdict([check], [], [], CheckStatus.PASSED)
    assert v == Verdict.INCOMPLETE

def test_verdict_verified():
    check = CheckResult(
        name="pytest", status=CheckStatus.PASSED,
        exit_code=0, duration=1.0, stdout="", stderr=""
    )
    v = determine_verdict([check], [], [], CheckStatus.PASSED)
    assert v == Verdict.VERIFIED
