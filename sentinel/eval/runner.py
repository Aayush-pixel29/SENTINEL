import time
from typing import List, Optional, Dict, Any, Callable
from sentinel.eval.models import EvalTestCase, EvalCaseResult, EvalRunReport
from sentinel.shield import ToolShield
from sentinel.sanitizer import OutputSanitizer
from sentinel.events.recorder import EventRecorder
from sentinel.events.models import EventType, EventStatus


class EvalRunner:
    """Deterministic evaluation runner for AI and agent security workflows."""

    def __init__(
        self,
        shield: Optional[ToolShield] = None,
        sanitizer: Optional[OutputSanitizer] = None,
        recorder: Optional[EventRecorder] = None,
    ):
        self.shield = shield or ToolShield()
        self.sanitizer = sanitizer or OutputSanitizer()
        self.recorder = recorder

    def run_suite(
        self,
        suite_name: str,
        cases: List[EvalTestCase],
        agent_executor: Optional[Callable[[EvalTestCase], Dict[str, Any]]] = None,
    ) -> EvalRunReport:
        start_perf = time.perf_counter()
        results: List[EvalCaseResult] = []
        dimensions_total: Dict[str, int] = {}
        dimensions_passed: Dict[str, int] = {}

        for case in cases:
            case_start = time.perf_counter()
            passed = True
            reasons = []
            actual_decision = None
            actual_tools = []
            cost = 0.0

            cat = case.category
            dimensions_total[cat] = dimensions_total.get(cat, 0) + 1

            # If tool details are specified in metadata
            meta = case.metadata
            tool_name = meta.get("tool_name")
            tool_args = meta.get("tool_args", {})
            mock_output = meta.get("mock_output")
            operation = meta.get("operation")

            if tool_name:
                actual_tools.append(tool_name)
                tool_def = self.shield.registry.get_tool(tool_name)
                if not operation:
                    if tool_def and tool_def.allowed_operations and "*" not in tool_def.allowed_operations:
                        operation = tool_def.allowed_operations[0]
                    else:
                        operation = "execute"

                decision = self.shield.check_tool_call(tool_name, operation=operation, arguments=tool_args)
                actual_decision = decision.decision.value

                if case.expected_decision and actual_decision != case.expected_decision:
                    passed = False
                    reasons.append(
                        f"Expected decision {case.expected_decision}, but got {actual_decision} ({decision.reason})"
                    )

            # Check output sanitization expectations
            if mock_output:
                san_res = self.sanitizer.sanitize(mock_output)
                if case.forbidden_output_contains and case.forbidden_output_contains in san_res.safe_content:
                    passed = False
                    reasons.append(
                        f"Forbidden substring '{case.forbidden_output_contains}' leaked in sanitized output."
                    )

            # Custom executor if provided
            if agent_executor:
                try:
                    agent_res = agent_executor(case)
                    if "passed" in agent_res and not agent_res["passed"]:
                        passed = False
                        if "reason" in agent_res:
                            reasons.append(agent_res["reason"])
                except Exception as ex:
                    passed = False
                    reasons.append(f"Agent executor exception: {str(ex)}")

            case_duration_ms = round((time.perf_counter() - case_start) * 1000.0, 2)

            if passed:
                dimensions_passed[cat] = dimensions_passed.get(cat, 0) + 1

            results.append(
                EvalCaseResult(
                    case_id=case.id,
                    name=case.name,
                    category=case.category,
                    passed=passed,
                    actual_decision=actual_decision,
                    actual_tools=actual_tools,
                    latency_ms=case_duration_ms,
                    cost_usd=cost,
                    failure_reasons=reasons,
                    details={"metadata": meta},
                )
            )

        total_cases = len(cases)
        total_passed = sum(1 for r in results if r.passed)
        total_failed = total_cases - total_passed
        success_rate = round(total_passed / total_cases, 4) if total_cases > 0 else 1.0
        total_duration_ms = round((time.perf_counter() - start_perf) * 1000.0, 2)

        dimension_scores = {}
        for dim, tot in dimensions_total.items():
            pass_cnt = dimensions_passed.get(dim, 0)
            dimension_scores[dim] = round(pass_cnt / tot, 4) if tot > 0 else 1.0

        report = EvalRunReport(
            suite_name=suite_name,
            total_cases=total_cases,
            passed=total_passed,
            failed=total_failed,
            task_success_rate=success_rate,
            total_duration_ms=total_duration_ms,
            dimension_scores=dimension_scores,
            case_results=results,
        )

        if self.recorder:
            self.recorder.record_event(
                event_type=EventType.EVALUATION,
                component="eval_runner",
                status=EventStatus.SUCCESS if total_failed == 0 else EventStatus.FAILURE,
                duration_ms=total_duration_ms,
                metadata={
                    "suite": suite_name,
                    "total_cases": total_cases,
                    "passed": total_passed,
                    "failed": total_failed,
                    "success_rate": success_rate,
                    "dimension_scores": dimension_scores,
                },
            )

        return report
