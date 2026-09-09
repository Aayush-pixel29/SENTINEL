import re
from sentinel.checks.base import BaseCheck
from sentinel.models import CheckResult, CheckStatus

class PytestCheck(BaseCheck):
    @property
    def name(self) -> str:
        return "pytest"

    def run(self) -> CheckResult:
        result = self.run_command(["pytest"])
        if result.status == CheckStatus.NOT_AVAILABLE or result.status == CheckStatus.ERROR:
            return result

        # Custom parsing for pytest output could go here to extract
        # the number of passed/failed tests and add them to stdout or metadata.
        # But keeping it simple for the MVP.
        return result
