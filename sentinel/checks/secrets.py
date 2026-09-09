import json
import tempfile
import os
from typing import List
from sentinel.checks.base import BaseCheck
from sentinel.models import CheckResult, CheckStatus, Finding, Classification

class GitleaksCheck(BaseCheck):
    @property
    def name(self) -> str:
        return "gitleaks"

    def run(self) -> CheckResult:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            report_path = tmp.name

        try:
            result = self.run_command([
                "gitleaks", "detect", 
                "--no-banner", 
                "--no-git", # run on directory since diff might be uncommitted
                "--report-format", "json",
                "--report-path", report_path,
                "."
            ])
            
            if result.status == CheckStatus.NOT_AVAILABLE:
                return result

            findings: List[Finding] = []
            if os.path.exists(report_path):
                with open(report_path, 'r') as f:
                    content = f.read()
                    if content:
                        try:
                            data = json.loads(content)
                            for match in data:
                                findings.append(Finding(
                                    id=f"gitleaks-{match.get('RuleID', 'unknown')}",
                                    source="gitleaks",
                                    classification=Classification.CONFIRMED,
                                    severity="CRITICAL", # Secrets are always high severity
                                    title=match.get("Description", "Secret exposed"),
                                    description=match.get("Description", "Secret exposed"),
                                    file=match.get("File"),
                                    line=match.get("StartLine"),
                                    # DO NOT INCLUDE THE SECRET IN EVIDENCE
                                    evidence="<REDACTED SECRET>"
                                ))
                        except json.JSONDecodeError:
                            pass

            if result.exit_code in [0, 1]:
                result.status = CheckStatus.PASSED if len(findings) == 0 else CheckStatus.FAILED
            else:
                result.status = CheckStatus.ERROR
                
            result.findings = findings
            return result
        finally:
            if os.path.exists(report_path):
                os.remove(report_path)
