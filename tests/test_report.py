import os
from sentinel.report.markdown import generate_markdown_report
from sentinel.report.json import generate_json_report
from sentinel.models import VerificationReport, Verdict, Finding, Classification


def test_generate_markdown_report(tmp_path):
    report_path = tmp_path / "report.md"
    report = VerificationReport(
        run_id="run_test_md_001",
        verdict=Verdict.VERIFIED,
        repository="test-repo",
        branch="main",
        commit="abc123",
        changed_files=["app.py"],
        checks=[],
        confirmed_findings=[],
        unconfirmed_findings=[],
        metrics={"model": "gemini-2.5-flash", "provider": "gemini", "input_tokens": 500, "output_tokens": 100, "total_tokens": 600, "latency_ms": 320.0, "estimated_cost_usd": 0.000067},
        tool_decisions=[{"tool": "read_repository", "decision": "ALLOW", "reason": "policy_verified_allowed", "risk": "low"}],
        eval_report={"suite_name": "Core Eval", "total_cases": 10, "passed": 10, "task_success_rate": 1.0},
    )
    generate_markdown_report(report, str(report_path))
    assert os.path.exists(report_path)
    content = report_path.read_text(encoding="utf-8")
    assert "VERIFIED" in content
    assert "test-repo" in content
    assert "run_test_md_001" in content
    assert "ToolShield Policy Decisions" in content
    assert "Cost & Latency Telemetry" in content
    assert "Deterministic Evaluation & Red Team Suite" in content


def test_generate_json_report(tmp_path):
    report_path = tmp_path / "report.json"
    report = VerificationReport(
        run_id="run_test_json_002",
        verdict=Verdict.BLOCKED,
        repository="test-repo",
        branch="feature",
        commit="def456",
        changed_files=["app.py"],
        checks=[],
        confirmed_findings=[],
        unconfirmed_findings=[],
    )
    generate_json_report(report, str(report_path))
    assert os.path.exists(report_path)
    content = report_path.read_text(encoding="utf-8")
    assert "BLOCKED" in content
    assert "test-repo" in content
    assert "run_test_json_002" in content


def test_no_secrets_in_report(tmp_path):
    """Ensure no API keys appear in the report."""
    report_path = tmp_path / "report.json"
    finding = Finding(
        id="1", source="gitleaks", classification=Classification.CONFIRMED,
        severity="CRITICAL", title="Secret", description="Found a key",
        evidence="<REDACTED SECRET>",
    )
    report = VerificationReport(
        verdict=Verdict.BLOCKED,
        confirmed_findings=[finding],
        changed_files=[],
        checks=[],
        unconfirmed_findings=[],
    )
    generate_json_report(report, str(report_path))
    content = report_path.read_text(encoding="utf-8")
    assert "REDACTED" in content
    assert "sk-" not in content
    assert "AKIA" not in content
