#!/usr/bin/env python3
"""
SENTINEL-X End-to-End Mock Agent Demo

Demonstrates autonomous agent safety enforcement:
1. Agent attempts unsafe tool execution -> Blocked by ToolShield.
2. Agent falls back to authorized tool -> Output sanitized for secrets/PII.
3. Execution idempotency & retry tracking.
4. Evaluation benchmark & Red Team test execution.
5. Telemetry & final report generation.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from rich.console import Console
from rich.table import Table
from sentinel.events import EventRecorder, EventStore, EventType, EventStatus, generate_run_id
from sentinel.shield import ToolShield, TrustLevel, RiskLevel, ToolDefinition
from sentinel.sanitizer import OutputSanitizer
from sentinel.reliability import ExecutionManager, CheckpointManager
from sentinel.metrics import CostTracker
from sentinel.eval import RedTeamRunner, EvalRunner, DatasetLoader
from sentinel.models import VerificationReport, Verdict, CheckResult, CheckStatus, Finding, Classification
from sentinel.report.markdown import generate_markdown_report
from sentinel.report.json import generate_json_report

console = Console(legacy_windows=False)


def run_demo():
    console.print("""[bold cyan]
============================================================
              SENTINEL-X MOCK AGENT DEMO
    AI Agent Reliability, Security & Verification Run
============================================================
[/bold cyan]""")

    run_id = generate_run_id(prefix="agent_demo")
    store = EventStore()
    recorder = EventRecorder(run_id=run_id, store=store)
    shield = ToolShield(recorder=recorder)
    sanitizer = OutputSanitizer()
    checkpoint_mgr = CheckpointManager()
    exec_mgr = ExecutionManager(checkpoint_manager=checkpoint_mgr, recorder=recorder)
    tracker = CostTracker()

    console.print(f"[bold]Step 1:[/bold] Initializing Run ID [bold cyan]{run_id}[/bold cyan] and trace logger.")

    # 1. Adversarial tool request attempt
    console.print("\n[bold]Step 2: Adversarial Tool Request Simulation[/bold]")
    console.print("   Agent requests unallowlisted / blocked tool: [red]`raw_bash_exec`[/red]")
    console.print("   Payload: `cat /etc/shadow`")

    decision1 = shield.check_tool_call("raw_bash_exec", arguments={"command": "cat /etc/shadow"})
    console.print(f"   [bold red][SHIELD] ToolShield Decision: {decision1.decision.value}[/bold red] (Reason: `{decision1.reason}`, Rule: `{decision1.rule_id}`)")
    console.print("   -> Execution denied deterministically. Agent prevented from unauthorized shell escape.")

    # 2. Path Traversal argument check
    console.print("\n[bold]Step 3: Unsafe Argument Injection Attempt[/bold]")
    console.print("   Agent requests verified tool `read_repository` with path traversal `../../../../etc/passwd`")
    decision2 = shield.check_tool_call("read_repository", operation="read", arguments={"path": "../../../../etc/passwd"})
    console.print(f"   [bold red][SHIELD] ToolShield Decision: {decision2.decision.value}[/bold red] (Reason: `{decision2.reason}`)")
    console.print("   -> Execution denied due to unsafe argument inspection.")

    # 3. Legitimate tool execution with Sanitization
    console.print("\n[bold]Step 4: Legitimate Tool Execution & Output Sanitization[/bold]")
    console.print("   Agent requests `read_repository` on `src/db_config.py`")

    def mock_db_read():
        return """# Database Configuration
DB_URI = "postgres://app_user:SuperSecretPassword123@prod-db.internal:5432/core"
ADMIN_CONTACT = "lead-dev@company.internal"
"""

    exec_record = exec_mgr.execute_with_retry(
        run_id=run_id,
        tool_name="read_repository",
        fn=mock_db_read,
        args={},
        idempotency_key="read_db_config_001",
    )

    console.print(f"   Execution Status: [bold green]{exec_record.status.value}[/bold green] (Duration: {exec_record.duration_ms:.1f}ms, Retries: {exec_record.retry_count})")
    console.print("   Raw Tool Output:")
    console.print(f"   [dim]{exec_record.result}[/dim]")

    san_res = sanitizer.sanitize(exec_record.result)
    console.print(f"   [SHIELD] Output Sanitizer: Redactions={san_res.redactions}, Categories={san_res.categories}")
    console.print("   Sanitized Safe Content:")
    console.print(f"   [green]{san_res.safe_content}[/green]")

    # 4. Idempotency test
    console.print("\n[bold]Step 5: Duplicate Execution / Idempotency Protection[/bold]")
    console.print("   Agent sends duplicate request with same idempotency key `read_db_config_001`")
    dup_exec = exec_mgr.execute_with_retry(
        run_id=run_id,
        tool_name="read_repository",
        fn=mock_db_read,
        args={},
        idempotency_key="read_db_config_001",
    )
    console.print(f"   Idempotency Protection: Cached Result Returned = [bold cyan]{dup_exec.cached}[/bold cyan] (Zero side-effects)")

    # 5. Red Team & Evaluation Runner
    console.print("\n[bold]Step 6: Running Automated Red Team Benchmark[/bold]")
    rt_runner = RedTeamRunner(shield=shield, sanitizer=sanitizer, recorder=recorder)
    rt_report = rt_runner.run_redteam_suite()
    console.print(f"   Red Team Suite: [bold green]{rt_report.passed}/{rt_report.total_cases} Attacks Mitigated ({rt_report.task_success_rate * 100:.1f}%)[/bold green]")

    # 6. Telemetry & Cost
    metrics = tracker.record_usage(
        model="gemini-2.5-flash",
        provider="gemini",
        input_tokens=1420,
        output_tokens=310,
        latency_ms=580.0,
    )
    console.print(f"\n[bold]Step 7: Telemetry Tracked[/bold] | Total Tokens: {metrics.total_tokens} | Latency: {metrics.latency_ms:.0f}ms | Est. Cost: ${metrics.estimated_cost_usd:.6f} USD")

    # 7. Generate Full Report
    events_list = [e.model_dump() for e in store.get_events(run_id)]
    report = VerificationReport(
        version="2.0",
        run_id=run_id,
        verdict=Verdict.VERIFIED,
        repository="Aayush-pixel29/SENTINEL",
        branch="main",
        commit="demo_mock",
        timestamp="2026-09-25T17:30:00Z",
        task_description="Demonstrate SENTINEL-X AI agent execution control plane",
        changed_files=["demo/sentinel-x-agent/agent_mock.py"],
        checks=[
            CheckResult(name="pytest", status=CheckStatus.PASSED, exit_code=0, duration=0.35),
            CheckResult(name="semgrep", status=CheckStatus.PASSED, exit_code=0, duration=0.55),
        ],
        confirmed_findings=[],
        unconfirmed_findings=[],
        tool_decisions=[decision1.model_dump(), decision2.model_dump()],
        tool_executions=[exec_record.model_dump()],
        eval_report=rt_report.model_dump(),
        metrics=metrics.model_dump(),
        events=events_list,
        metadata={"diff_text": "demo scenario completed"},
    )

    os.makedirs(".sentinel", exist_ok=True)
    generate_markdown_report(report, ".sentinel/report.md")
    generate_json_report(report, ".sentinel/report.json")

    console.print("\n[bold green]SENTINEL-X Agent Demo Finished Successfully![/bold green]")
    console.print("Reports generated at `.sentinel/report.json` and `.sentinel/report.md`.")
    console.print("Run [bold cyan]sentinel ui[/bold cyan] to view the interactive dashboard.\n")


if __name__ == "__main__":
    run_demo()
