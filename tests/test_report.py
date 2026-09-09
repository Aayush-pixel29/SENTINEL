import os
from sentinel.report.markdown import generate_markdown_report
from sentinel.report.json import generate_json_report
from sentinel.models import VerificationReport, Verdict, Finding, Classification


def test_generate_markdown_report(tmp_path):
    report_path = tmp_path / "report.md"
    report = VerificationReport(
        verdict=Verdict.VERIFIED,
        repository="test-repo",
        branch="main",
        commit="abc123",
        changed_files=["app.py"],
        checks=[],
        confirmed_findings=[],
        unconfirmed_findings=[],
    )
    generate_markdown_report(report, str(report_path))
    assert os.path.exists(report_path)
    content = report_path.read_text()
    assert "VERIFIED" in content
    assert "test-repo" in content


def test_generate_json_report(tmp_path):
    report_path = tmp_path / "report.json"
    report = VerificationReport(
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
    content = report_path.read_text()
    assert "BLOCKED" in content
    assert "test-repo" in content


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
    content = report_path.read_text()
    assert "REDACTED" in content
    # Ensure no actual key patterns leak
    assert "sk-" not in content
    assert "AKIA" not in content
