import os
from sentinel.report.markdown import generate_markdown_report
from sentinel.report.json import generate_json_report
from sentinel.models import VerificationReport, Verdict

def test_generate_markdown_report(tmp_path):
    report_path = tmp_path / "report.md"
    
    report = VerificationReport(
        verdict=Verdict.VERIFIED,
        changed_files=["app.py"],
        checks=[],
        confirmed_findings=[],
        unconfirmed_findings=[],
        ai_review={}
    )
    
    generate_markdown_report(report, str(report_path))
    assert os.path.exists(report_path)
    content = report_path.read_text()
    assert "VERIFIED" in content

def test_generate_json_report(tmp_path):
    report_path = tmp_path / "report.json"
    
    report = VerificationReport(
        verdict=Verdict.BLOCKED,
        changed_files=["app.py"],
        checks=[],
        confirmed_findings=[],
        unconfirmed_findings=[],
        ai_review={}
    )
    
    generate_json_report(report, str(report_path))
    assert os.path.exists(report_path)
    content = report_path.read_text()
    assert "BLOCKED" in content
