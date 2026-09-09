from sentinel.checks.base import BaseCheck
from sentinel.models import CheckResult, CheckStatus

class RuffCheck(BaseCheck):
    @property
    def name(self) -> str:
        return "ruff"

    def run(self) -> CheckResult:
        return self.run_command(["ruff", "check", "."])
