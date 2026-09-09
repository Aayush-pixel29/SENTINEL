import json
from typing import List
from sentinel.checks.base import BaseCheck
from sentinel.models import CheckResult, CheckStatus, Finding, Classification

class PipAuditCheck(BaseCheck):
    @property
    def name(self) -> str:
        return "pip-audit"

    def run(self) -> CheckResult:
        result = self.run_command(["pip-audit", "-f", "json"])
        
        if result.status == CheckStatus.NOT_AVAILABLE:
            return result

        findings: List[Finding] = []
        try:
            data = json.loads(result.stdout)
            for pkg in data.get("dependencies", []):
                vulns = pkg.get("vulns", [])
                for vuln in vulns:
                    findings.append(Finding(
                        id=vuln.get("id", "unknown"),
                        source="pip-audit",
                        classification=Classification.CONFIRMED,
                        severity="HIGH",
                        title=f"Vulnerable Dependency: {pkg.get('name')}",
                        description=vuln.get("fix_versions", ["No fix available"])[0],
                        file="requirements.txt", # Approximation
                        evidence=f"Package {pkg.get('name')} v{pkg.get('version')} has {vuln.get('id')}"
                    ))
            
            if result.exit_code in [0, 1]:
                result.status = CheckStatus.PASSED if len(findings) == 0 else CheckStatus.FAILED
            else:
                result.status = CheckStatus.ERROR
        except json.JSONDecodeError:
            if result.exit_code != 0:
                result.status = CheckStatus.ERROR
                
        result.findings = findings
        return result
