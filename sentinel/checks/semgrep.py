import json
from typing import List
from sentinel.checks.base import BaseCheck
from sentinel.models import CheckResult, CheckStatus, Finding, Classification

class SemgrepCheck(BaseCheck):
    @property
    def name(self) -> str:
        return "semgrep"

    def run(self) -> CheckResult:
        result = self.run_command(["semgrep", "--config", "auto", "--json", "."])
        
        if result.status == CheckStatus.NOT_AVAILABLE:
            return result

        findings: List[Finding] = []
        try:
            # semgrep returns JSON on stdout
            data = json.loads(result.stdout)
            for match in data.get("results", []):
                findings.append(Finding(
                    id=f"semgrep-{match.get('check_id', 'unknown')}",
                    source="semgrep",
                    classification=Classification.CONFIRMED,
                    severity=match.get("extra", {}).get("severity", "WARNING"),
                    title=match.get("check_id", "Semgrep Finding"),
                    description=match.get("extra", {}).get("message", "No description"),
                    file=match.get("path"),
                    line=match.get("start", {}).get("line"),
                    evidence=match.get("extra", {}).get("lines")
                ))
            
            # Semgrep exits with 1 if there are findings
            if result.exit_code in [0, 1]:
                result.status = CheckStatus.PASSED if len(findings) == 0 else CheckStatus.FAILED
            else:
                result.status = CheckStatus.ERROR
        except json.JSONDecodeError:
            if result.exit_code != 0:
                result.status = CheckStatus.ERROR
        
        result.findings = findings
        return result
