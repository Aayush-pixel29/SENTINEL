import json
import os
import time
import webbrowser
import http.server
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from sentinel.config import load_config
from sentinel.git.diff import get_git_diff, get_current_branch, get_current_commit, get_repo_name
from sentinel.checks.tests import PytestCheck
from sentinel.checks.lint import RuffCheck
from sentinel.checks.typecheck import MypyCheck
from sentinel.checks.semgrep import SemgrepCheck
from sentinel.checks.secrets import GitleaksCheck
from sentinel.checks.dependencies import PipAuditCheck
from sentinel.engine.evidence import get_confirmed_findings, get_unconfirmed_findings, gather_evidence_context
from sentinel.engine.verdict import determine_verdict
from sentinel.ai.critic import run_ai_review
from sentinel.models import VerificationReport, CheckStatus, Verdict
from sentinel.report.markdown import generate_markdown_report
from sentinel.report.json import generate_json_report
from sentinel.events import EventRecorder, EventStore, EventType, EventStatus, generate_run_id
from sentinel.shield import ToolShield, TrustLevel, RiskLevel
from sentinel.sanitizer import OutputSanitizer
from sentinel.metrics import PricingAdapter, CostTracker, ExecutionMetrics
from sentinel.eval import EvalRunner, RedTeamRunner, DatasetLoader

app = typer.Typer(help="SENTINEL-X - AI Agent Reliability, Security & Verification Control Plane")
console = Console()


@app.command()
def verify(
    config: str = typer.Option(".sentinel/config.yml", help="Path to config file"),
    run_eval: bool = typer.Option(False, "--eval", help="Run deterministic evaluation suite alongside verification"),
):
    """Run Sentinel-X verification pipeline on current Git changes."""

    run_id = generate_run_id()
    event_store = EventStore()
    recorder = EventRecorder(run_id=run_id, store=event_store)
    cost_tracker = CostTracker()

    console.print("""[bold cyan]
------------------------------------------------------------
                    S E N T I N E L - X
    AI Agent Reliability, Security & Verification Control Plane
------------------------------------------------------------
[/bold cyan]""")

    settings = load_config(config)

    # -- Git metadata ----------------------------------------------------------
    repo_name = get_repo_name()
    branch = get_current_branch()
    commit = get_current_commit()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    console.print(f"  Run ID       [bold cyan]{run_id}[/bold cyan]")
    console.print(f"  Repository   [bold]{repo_name}[/bold]")
    console.print(f"  Branch       {branch}")
    console.print(f"  Commit       {commit}")
    console.print()

    recorder.record_event(
        event_type=EventType.RUN,
        component="pipeline",
        status=EventStatus.RUNNING,
        metadata={"repo": repo_name, "branch": branch, "commit": commit},
    )

    # -- Git diff --------------------------------------------------------------
    console.print("Analyzing Git changes ...")
    start_diff = time.perf_counter()
    try:
        diff = get_git_diff()
        diff_duration_ms = (time.perf_counter() - start_diff) * 1000.0
        recorder.record_event(
            event_type=EventType.GIT_DIFF,
            component="git",
            status=EventStatus.SUCCESS,
            duration_ms=round(diff_duration_ms, 2),
            metadata={"files_changed": diff.files_changed, "lines_added": diff.lines_added, "lines_removed": diff.lines_removed},
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        recorder.record_event(
            event_type=EventType.ERROR,
            component="git",
            status=EventStatus.FAILURE,
            error=str(e),
        )
        raise typer.Exit(1)

    if diff.files_changed == 0:
        console.print("[yellow]No changes detected.[/yellow] Stage or modify files first.")
        raise typer.Exit(0)

    console.print(f"\n[bold]CHANGE[/bold]  ({diff.diff_source})")
    console.print(f"  Files changed     {diff.files_changed}")
    console.print(f"  Lines added       +{diff.lines_added}")
    console.print(f"  Lines removed     -{diff.lines_removed}")

    # -- Deterministic checks --------------------------------------------------
    console.print("\n[bold]DETERMINISTIC CHECKS[/bold]\n")

    check_runners = []
    if settings.checks.test.enabled:
        check_runners.append(PytestCheck())
    if settings.checks.lint.enabled:
        check_runners.append(RuffCheck())
    if settings.checks.typecheck.enabled:
        check_runners.append(MypyCheck())
    if settings.checks.semgrep.enabled:
        check_runners.append(SemgrepCheck())
    if settings.checks.secrets.enabled:
        check_runners.append(GitleaksCheck())
    if settings.checks.dependencies.enabled:
        check_runners.append(PipAuditCheck())

    results = []
    for runner in check_runners:
        with console.status(f"Running {runner.name} ..."):
            res = runner.run()
            results.append(res)
            
            evt_status = EventStatus.SUCCESS if res.status == CheckStatus.PASSED else EventStatus.FAILURE
            recorder.record_event(
                event_type=EventType.TEST if runner.name == "pytest" else EventType.SEMGREP if runner.name == "semgrep" else EventType.SECRET_SCAN if runner.name == "gitleaks" else EventType.POLICY_CHECK,
                component=runner.name,
                status=evt_status,
                duration_ms=round(res.duration * 1000.0, 2),
                metadata={"findings_count": len(res.findings), "exit_code": res.exit_code},
            )

            if res.status == CheckStatus.PASSED:
                icon = "[green]PASS[/green]"
            elif res.status == CheckStatus.FAILED:
                n = len(res.findings)
                icon = f"[red]FAIL[/red]  {n} finding(s)" if n else "[red]FAIL[/red]"
            else:
                icon = f"[dim]{res.status.value}[/dim]"
            console.print(f"  {runner.name.ljust(16)} {icon}")

    confirmed = get_confirmed_findings(results)

    # -- AI critic -------------------------------------------------------------
    console.print("\n[bold]AI REVIEW[/bold]\n")

    ai_result = None
    unconfirmed = []
    metrics = None

    if settings.ai.enabled:
        with console.status("Running independent AI review (Gemini) ..."):
            start_ai = time.perf_counter()
            context = gather_evidence_context(diff, results, settings.task.description)
            ai_result = run_ai_review(context)
            ai_duration_ms = (time.perf_counter() - start_ai) * 1000.0
            unconfirmed = get_unconfirmed_findings(ai_result)

            # Heuristic token count for telemetry
            in_tokens = int(len(context) / 4.0)
            out_tokens = int(len(ai_result.summary) / 4.0) + (len(unconfirmed) * 60)
            metrics = cost_tracker.record_usage(
                model="gemini-2.5-flash",
                provider="gemini",
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                latency_ms=ai_duration_ms,
            )

            recorder.record_event(
                event_type=EventType.LLM_CALL,
                component="ai_critic",
                status=EventStatus.SUCCESS if ai_result.status == CheckStatus.PASSED else EventStatus.FAILURE,
                duration_ms=round(ai_duration_ms, 2),
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                estimated_cost_usd=metrics.estimated_cost_usd,
                metadata={"unconfirmed_findings": len(unconfirmed)},
            )

            if ai_result.status == CheckStatus.PASSED:
                if unconfirmed:
                    console.print(f"  [yellow]{len(unconfirmed)} unconfirmed concern(s)[/yellow]")
                else:
                    console.print("  [green]No concerns raised[/green]")
            elif ai_result.status == CheckStatus.NOT_AVAILABLE:
                console.print(f"  [dim]Unavailable: {ai_result.summary}[/dim]")
            else:
                console.print(f"  [red]Error: {ai_result.summary}[/red]")
    else:
        console.print("  [dim]AI review disabled in config[/dim]")

    # -- Optional Evaluation Suite ---------------------------------------------
    eval_report = None
    if run_eval:
        console.print("\n[bold]EVALUATION SUITE[/bold]\n")
        with console.status("Running deterministic evaluation cases ..."):
            eval_runner = EvalRunner(recorder=recorder)
            default_cases = DatasetLoader.load_default_cases()
            eval_report = eval_runner.run_suite("Verification Baseline", default_cases)
            console.print(f"  Pass Rate: [bold cyan]{eval_report.task_success_rate * 100:.1f}%[/bold cyan] ({eval_report.passed}/{eval_report.total_cases})")

    # -- Verdict ---------------------------------------------------------------
    console.print("\n------------------------------------------------------------\n")

    ai_status = ai_result.status if ai_result else CheckStatus.SKIPPED
    verdict = determine_verdict(results, confirmed, unconfirmed, ai_status)

    console.print("[bold]VERDICT[/bold]\n")
    verdict_display = {
        "BLOCKED":    "  [bold red]BLOCKED[/bold red]",
        "REVIEW":     "  [bold yellow]REVIEW[/bold yellow]",
        "INCOMPLETE": "  [dim]INCOMPLETE[/dim]",
        "VERIFIED":   "  [bold green]VERIFIED[/bold green]",
    }
    console.print(verdict_display.get(verdict.value, verdict.value))
    console.print()

    # -- Findings summary ------------------------------------------------------
    if confirmed:
        console.print("[bold]CONFIRMED (Deterministic)[/bold]\n")
        for f in confirmed:
            loc = f"  {f.file}:{f.line}" if f.file else ""
            console.print(f"  [red]{f.title}[/red]{loc}")
            console.print(f"     Detected by {f.source}\n")

    if unconfirmed:
        console.print("[bold]UNCONFIRMED (AI Critic)[/bold]\n")
        for f in unconfirmed:
            loc = f"  {f.file}:{f.line}" if f.file else ""
            console.print(f"  [yellow]{f.title}[/yellow]{loc}")
            if f.recommendation:
                console.print(f"     {f.recommendation}")
            console.print()

    if metrics:
        console.print(f"[dim]Telemetry: {metrics.latency_ms:.0f}ms latency | ~{metrics.total_tokens} tokens | ~${metrics.estimated_cost_usd:.5f} USD[/dim]\n")

    console.print("------------------------------------------------------------\n")

    # -- Reports ---------------------------------------------------------------
    events_list = [e.model_dump() for e in event_store.get_events(run_id)]

    report = VerificationReport(
        version="2.0",
        run_id=run_id,
        verdict=verdict,
        repository=repo_name,
        branch=branch,
        commit=commit,
        timestamp=timestamp,
        task_description=settings.task.description,
        changed_files=diff.changed_files_list,
        checks=results,
        confirmed_findings=confirmed,
        unconfirmed_findings=unconfirmed,
        ai_review=ai_result.model_dump() if ai_result else {"summary": "Disabled"},
        ai_provider=ai_result.provider if ai_result else "",
        eval_report=eval_report.model_dump() if eval_report else None,
        metrics=metrics.model_dump() if metrics else None,
        events=events_list,
        metadata={"diff_text": diff.diff_text},
    )

    os.makedirs(".sentinel", exist_ok=True)
    generate_markdown_report(report, ".sentinel/report.md")
    generate_json_report(report, ".sentinel/report.json")

    console.print("Reports:")
    console.print("  .sentinel/report.md")
    console.print("  .sentinel/report.json")
    console.print(f"  .sentinel/events/{run_id}.jsonl")
    console.print("\nRun [bold]sentinel ui[/bold] to open the verification dashboard.\n")


@app.command()
def eval(dataset: Optional[str] = typer.Argument(None, help="Optional path to custom JSON evaluation dataset")):
    """Run deterministic evaluation benchmark suite."""
    console.print("[bold cyan]Running SENTINEL-X Evaluation Suite...[/bold cyan]\n")
    runner = EvalRunner()
    if dataset:
        cases = DatasetLoader.load_from_file(dataset)
    else:
        cases = DatasetLoader.load_default_cases()

    if not cases:
        console.print("[red]No test cases loaded.[/red]")
        raise typer.Exit(1)

    report = runner.run_suite("CLI Evaluation Suite", cases)

    table = Table(title=f"Evaluation Results: {report.suite_name}")
    table.add_column("Case ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Category", style="magenta")
    table.add_column("Decision", style="yellow")
    table.add_column("Status", style="bold")

    for c in report.case_results:
        status = "[green]PASS[/green]" if c.passed else "[red]FAIL[/red]"
        table.add_row(c.case_id, c.name, c.category, c.actual_decision or "-", status)

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {report.total_cases} | [green]Passed:[/green] {report.passed} | [red]Failed:[/red] {report.failed} | [bold cyan]Success Rate: {report.task_success_rate * 100:.1f}%[/bold cyan]\n")


@app.command()
def redteam():
    """Run full adversarial Red Team security test corpus."""
    console.print("[bold red]------------------------------------------------------------[/bold red]")
    console.print("[bold red]       SENTINEL-X ADVERSARIAL RED TEAM SUITE                [/bold red]")
    console.print("[bold red]------------------------------------------------------------[/bold red]\n")

    runner = RedTeamRunner()
    report = runner.run_redteam_suite()

    table = Table(title="Red Team Defense Evaluation")
    table.add_column("Case ID", style="cyan")
    table.add_column("Attack Vector", style="white")
    table.add_column("Category", style="magenta")
    table.add_column("Defense Outcome", style="bold")

    for c in report.case_results:
        outcome = "[green]MITIGATED / BLOCKED[/green]" if c.passed else "[red]VULNERABLE[/red]"
        table.add_row(c.case_id, c.name, c.category, outcome)

    console.print(table)
    console.print(f"\n[bold]Total Attacks Tested:[/bold] {report.total_cases}")
    console.print(f"[bold green]Attacks Mitigated:[/bold green] {report.passed}/{report.total_cases} ({report.task_success_rate * 100:.1f}%)\n")


@app.command()
def trace(run_id: Optional[str] = typer.Argument(None, help="Run ID to inspect")):
    """Inspect event spans and timeline for a verification run."""
    store = EventStore()
    if not run_id:
        runs = store.list_runs()
        if not runs:
            console.print("[yellow]No runs found in .sentinel/events/[/yellow]")
            return
        console.print("[bold cyan]Recent Runs:[/bold cyan]")
        for r in runs[-10:]:
            console.print(f"  - {r}")
        console.print("\nRun [bold]sentinel trace <run_id>[/bold] to view event timeline.")
        return

    events = store.get_events(run_id)
    if not events:
        console.print(f"[red]No trace events found for run '{run_id}'[/red]")
        return

    table = Table(title=f"Trace Waterfall for {run_id}")
    table.add_column("Event ID", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Component", style="white")
    table.add_column("Status", style="bold")
    table.add_column("Duration", style="yellow")
    table.add_column("Cost USD", style="green")

    for e in events:
        st_color = "green" if e.status == EventStatus.SUCCESS else "red" if e.status in (EventStatus.FAILURE, EventStatus.ERROR, EventStatus.BLOCKED) else "yellow"
        dur_str = f"{e.duration_ms:.1f}ms" if e.duration_ms is not None else "-"
        cost_str = f"${e.estimated_cost_usd:.6f}" if e.estimated_cost_usd else "-"
        table.add_row(e.event_id, e.event_type.value, e.component, f"[{st_color}]{e.status.value}[/{st_color}]", dur_str, cost_str)

    console.print(table)


@app.command(name="demo-agent")
def demo_agent():
    """Run local mock AI agent demonstrating ToolShield, Sanitization & Telemetry."""
    console.print("[bold cyan]Starting SENTINEL-X End-to-End Agent Execution Demo...[/bold cyan]\n")

    run_id = generate_run_id(prefix="demo")
    recorder = EventRecorder(run_id=run_id)
    shield = ToolShield(recorder=recorder)
    sanitizer = OutputSanitizer()
    tracker = CostTracker()

    console.print(f"[bold]1. Initializing Agent Run:[/bold] [cyan]{run_id}[/cyan]")

    # Step 1: Agent tries to invoke dangerous tool
    console.print("\n[bold]2. Agent requests unallowlisted / dangerous tool:[/bold] `raw_bash_exec`")
    decision1 = shield.check_tool_call("raw_bash_exec", arguments={"command": "cat /etc/shadow"})
    console.print(f"   ToolShield Decision: [bold red]{decision1.decision.value}[/bold red] (Reason: `{decision1.reason}`)")
    console.print("   -> Execution halted by policy boundary. Adversarial request prevented.")

    # Step 2: Agent falls back to authorized tool
    console.print("\n[bold]3. Agent falls back to verified tool:[/bold] `read_repository` (operation: `read`)")
    decision2 = shield.check_tool_call("read_repository", operation="read", arguments={"path": "src/config.py"})
    console.print(f"   ToolShield Decision: [bold green]{decision2.decision.value}[/bold green] (Reason: `{decision2.reason}`)")

    # Step 3: Raw output contains sensitive connection credentials -> Sanitizer triggers
    raw_output = "Configuration loaded:\npostgres://db_admin:VerySecretPass999@prod-cluster.internal:5432/app"
    console.print("\n[bold]4. Tool returns raw output containing database credentials:[/bold]")
    console.print(f"   [dim]{raw_output}[/dim]")

    san_res = sanitizer.sanitize(raw_output)
    console.print("\n[bold]5. SENTINEL-X Output Sanitizer Interception:[/bold]")
    console.print(f"   Sanitized: [bold cyan]{san_res.sanitized}[/bold cyan] | Redactions: {san_res.redactions} | Categories: {san_res.categories}")
    console.print("   Safe Content:")
    console.print(f"   [green]{san_res.safe_content}[/green]")

    # Step 4: Red team verification
    console.print("\n[bold]6. Running Red Team Benchmark against agent flow...[/bold]")
    rt_runner = RedTeamRunner(shield=shield, sanitizer=sanitizer, recorder=recorder)
    rt_report = rt_runner.run_redteam_suite()
    console.print(f"   Red Team Pass Rate: [bold green]{rt_report.task_success_rate * 100:.1f}%[/bold green] ({rt_report.passed}/{rt_report.total_cases})")

    # Step 5: Cost & Telemetry
    metrics = tracker.record_usage("gemini-2.5-flash", "gemini", input_tokens=850, output_tokens=180, latency_ms=420.0)
    console.print(f"\n[bold]7. Telemetry Recorded:[/bold] {metrics.latency_ms}ms | ~{metrics.total_tokens} tokens | ${metrics.estimated_cost_usd:.6f} USD")

    console.print("\n[bold green]Demo Completed Successfully.[/bold green] All traces recorded in local event store.\n")


@app.command()
def declare():
    """Generate an AI Use Declaration from the latest verification report."""

    report_path = Path(".sentinel/report.json")
    if not report_path.exists():
        console.print("[bold red]Error:[/bold red] No verification report found. Run [bold]sentinel verify[/bold] first.")
        raise typer.Exit(1)

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    checks = [c["name"] for c in data.get("checks", [])]
    provider = data.get("ai_provider", "Gemini")
    if not provider:
        provider = "Gemini"

    declaration = f"""# AI Use Declaration

## Project
{data.get("repository", "unknown")}

## Verification Run
- Run ID: {data.get("run_id", "unknown")}
- Branch: {data.get("branch", "unknown")}
- Commit: {data.get("commit", "unknown")}
- Timestamp: {data.get("timestamp", "unknown")}
- Verdict: **{data.get("verdict", "unknown")}**

## AI Tools Used
- {provider.capitalize()} (independent code review)

## AI-Assisted Work
- Code review and reasoning
- Potential issue identification
- Security, edge-case, and specification-mismatch analysis

## Automated Verification (Deterministic)
{chr(10).join([f"- {c}" for c in checks])}

## Human Verification
The developer reviewed the generated findings,
validated changes, and made the final decision
about whether the software was ready to merge.

## Limitations
- AI findings are labelled UNCONFIRMED and are not treated as proof.
- Deterministic findings are labelled CONFIRMED and reported separately.
- A clean report does not guarantee completely secure software.
- Only the checks listed above were executed.
"""
    with open("AI_USE_DECLARATION.md", "w", encoding="utf-8") as f:
        f.write(declaration)

    console.print("Created [bold]AI_USE_DECLARATION.md[/bold]")


@app.command()
def ui(port: int = typer.Option(5000, help="Port for the local dashboard")):
    """Open the local verification dashboard in the browser."""

    report_path = Path(".sentinel/report.json")
    if not report_path.exists():
        console.print("[bold red]Error:[/bold red] No verification report found. Run [bold]sentinel verify[/bold] first.")
        raise typer.Exit(1)

    with open(report_path, "r", encoding="utf-8") as f:
        report_data = f.read()

    from sentinel.ui.template import build_html
    html_content = build_html(report_data)

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))

        def log_message(self, format, *args):
            pass  # Silence request logs

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)

    url = f"http://127.0.0.1:{port}"
    console.print(f"Sentinel-X dashboard running at [bold cyan]{url}[/bold cyan]")
    console.print("Press Ctrl+C to stop.\n")
    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("\nDashboard stopped.")
        server.server_close()


@app.command()
def explain():
    """Explain the verification verdict in plain english."""
    report_path = Path(".sentinel/report.json")
    if not report_path.exists():
        console.print("[bold red]Error:[/bold red] No verification report found. Run [bold]sentinel verify[/bold] first.")
        raise typer.Exit(1)

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    verdict = data.get("verdict", "UNKNOWN")
    confirmed = data.get("confirmed_findings", [])
    unconfirmed = data.get("unconfirmed_findings", [])
    checks = data.get("checks", [])

    if verdict == "VERIFIED":
        console.print("\n[bold green]WHY VERIFIED[/bold green]")
        console.print("1. All required deterministic checks passed.")
        console.print("2. Gemini raised no significant concerns.")
        console.print("\n[bold]Recommended action:[/bold] Human review is still recommended before merging.")
        console.print()
        return

    title = "WHY BLOCKED" if verdict == "BLOCKED" else f"WHY {verdict}"
    color = "red" if verdict == "BLOCKED" else "yellow"
    
    console.print(f"\n[bold {color}]{title}[/bold {color}]")
    idx = 1
    
    for f in confirmed:
        loc = f.get("file", "unknown")
        console.print(f"{idx}. {f.get('source')} confirmed a {f.get('severity')} severity {f.get('title')} in {loc}.")
        idx += 1
        
    for f in unconfirmed:
        console.print(f"{idx}. Gemini identified a possible {f.get('title', '').lower()}. This is [yellow]UNCONFIRMED[/yellow].")
        idx += 1
        
    failed_checks = [c["name"] for c in checks if c["status"] == "FAILED"]
    passed_checks = [c["name"] for c in checks if c["status"] == "PASSED"]
    
    if failed_checks:
        console.print(f"{idx}. The following checks failed: {', '.join(failed_checks)}.")
        idx += 1
    elif passed_checks:
        console.print(f"{idx}. {len(passed_checks)} tests passed, but passing tests do not prove correctness.")
        idx += 1

    console.print("\n[bold]Recommended action:[/bold]", end=" ")
    if confirmed or failed_checks:
        console.print(f"[bold {color}]Fix the confirmed issues and failing checks, then re-run `sentinel verify`.[/bold {color}]")
    else:
        console.print(f"[bold {color}]Manually verify the AI concerns and decide whether to proceed.[/bold {color}]")
    console.print()


def main():
    app()


if __name__ == "__main__":
    main()
