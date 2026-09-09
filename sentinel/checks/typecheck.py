from sentinel.checks.base import BaseCheck
from sentinel.models import CheckResult

class MypyCheck(BaseCheck):
    @property
    def name(self) -> str:
        return "mypy"

    def run(self) -> CheckResult:
        return self.run_command(["mypy", "."])
