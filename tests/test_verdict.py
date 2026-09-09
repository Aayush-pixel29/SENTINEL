from sentinel.engine.verdict import determine_verdict
from sentinel.models import CheckResult, CheckStatus, Finding, Verdict, Classification


def test_verdict_blocked_by_critical_finding():
    finding = Finding(
        id="1", source="semgrep", classification=Classification.CONFIRMED,
        severity="CRITICAL", title="SQLi", description="SQL injection",
    )
    v = determine_verdict([], [finding], [], CheckStatus.PASSED)
    assert v == Verdict.BLOCKED


def test_verdict_blocked_by_high_finding():
    finding = Finding(
        id="1", source="semgrep", classification=Classification.CONFIRMED,
        severity="HIGH", title="XSS", description="XSS",
    )
    v = determine_verdict([], [finding], [], CheckStatus.PASSED)
    assert v == Verdict.BLOCKED


def test_verdict_blocked_by_failed_tests():
    check = CheckResult(
        name="pytest", status=CheckStatus.FAILED,
        exit_code=1, duration=1.0,
    )
    v = determine_verdict([check], [], [], CheckStatus.PASSED)
    assert v == Verdict.BLOCKED


def test_verdict_review_for_unconfirmed():
    finding = Finding(
        id="2", source="ai-critic", classification=Classification.UNCONFIRMED,
        severity="MEDIUM", title="Auth issue", description="Possible auth issue",
    )
    v = determine_verdict([], [], [finding], CheckStatus.PASSED)
    assert v == Verdict.REVIEW


def test_verdict_incomplete_for_missing_tool():
    check = CheckResult(
        name="semgrep", status=CheckStatus.NOT_AVAILABLE,
        exit_code=-1, duration=0,
    )
    v = determine_verdict([check], [], [], CheckStatus.PASSED)
    assert v == Verdict.INCOMPLETE


def test_verdict_incomplete_for_ai_unavailable():
    check = CheckResult(
        name="pytest", status=CheckStatus.PASSED,
        exit_code=0, duration=1.0,
    )
    v = determine_verdict([check], [], [], CheckStatus.NOT_AVAILABLE)
    assert v == Verdict.INCOMPLETE


def test_verdict_verified():
    check = CheckResult(
        name="pytest", status=CheckStatus.PASSED,
        exit_code=0, duration=1.0,
    )
    v = determine_verdict([check], [], [], CheckStatus.PASSED)
    assert v == Verdict.VERIFIED
