import subprocess
import time
from abc import ABC, abstractmethod
from typing import List

from sentinel.models import CheckResult, CheckStatus, Finding, Classification

class BaseCheck(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def run(self) -> CheckResult:
        pass

    def run_command(self, cmd: List[str]) -> CheckResult:
        start_time = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            duration = time.time() - start_time
            return CheckResult(
                name=self.name,
                status=CheckStatus.PASSED if result.returncode == 0 else CheckStatus.FAILED,
                exit_code=result.returncode,
                duration=duration,
                stdout=result.stdout,
                stderr=result.stderr,
                findings=[]
            )
        except FileNotFoundError:
            return CheckResult(
                name=self.name,
                status=CheckStatus.NOT_AVAILABLE,
                exit_code=-1,
                duration=0.0,
                stdout="",
                stderr=f"Command not found: {cmd[0]}",
                findings=[]
            )
        except Exception as e:
            return CheckResult(
                name=self.name,
                status=CheckStatus.ERROR,
                exit_code=-1,
                duration=time.time() - start_time,
                stdout="",
                stderr=str(e),
                findings=[]
            )
