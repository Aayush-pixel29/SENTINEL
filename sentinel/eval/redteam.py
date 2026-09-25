from typing import Optional
from sentinel.eval.models import EvalRunReport
from sentinel.eval.dataset import DatasetLoader
from sentinel.eval.runner import EvalRunner
from sentinel.shield import ToolShield
from sentinel.sanitizer import OutputSanitizer
from sentinel.events.recorder import EventRecorder


class RedTeamRunner:
    """Automated security red-team harness testing agent defenses against adversarial vectors."""

    def __init__(
        self,
        shield: Optional[ToolShield] = None,
        sanitizer: Optional[OutputSanitizer] = None,
        recorder: Optional[EventRecorder] = None,
    ):
        self.runner = EvalRunner(
            shield=shield or ToolShield(),
            sanitizer=sanitizer or OutputSanitizer(),
            recorder=recorder,
        )

    def run_redteam_suite(self) -> EvalRunReport:
        cases = DatasetLoader.load_redteam_cases()
        return self.runner.run_suite(suite_name="RedTeam Security Corpus", cases=cases)
