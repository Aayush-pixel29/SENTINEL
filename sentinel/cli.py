import json
import os
import webbrowser
import http.server
import threading
from pathlib import Path
from datetime import datetime, timezone

import typer
from rich.console import Console

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
from sentinel.models import VerificationReport, CheckStatus
from sentinel.report.markdown import generate_markdown_report
from sentinel.report.json import generate_json_report

app = typer.Typer(help="Sentinel - Evidence-driven verification for AI-generated code")
console = Console()


@app.command()
def verify(config: str = typer.Option(".sentinel/config.yml", help="Path to config file")):
    """Run Sentinel verification pipeline on current Git changes."""

    console.print("""[bold cyan]
----------------------------------------------
              S E N T I N E L
     Evidence-driven code verification
----------------------------------------------
[/bold cyan]""")

    settings = load_config(config)

    # -- Git metadata ----------------------------------------------------------
    repo_name = get_repo_name()
    branch = get_current_branch()
    commit = get_current_commit()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    console.print(f"  Repository   [bold]{repo_name}[/bold]")
    console.print(f"  Branch       {branch}")
    console.print(f"  Commit       {commit}")
    console.print()

    # -- Git diff --------------------------------------------------------------
    console.print("Analyzing Git changes ...")
    try:
        diff = get_git_diff()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
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
            if res.status == CheckStatus.PASSED:
                icon, style = "[green]PASS[/green]", "green"
            elif res.status == CheckStatus.FAILED:
                n = len(res.findings)
                icon = f"[red]FAIL[/red]  {n} finding(s)" if n else "[red]FAIL[/red]"
                style = "red"
            else:
                icon, style = f"[dim]{res.status.value}[/dim]", "dim"
            console.print(f"  {runner.name.ljust(16)} {icon}")

    confirmed = get_confirmed_findings(results)

    # -- AI critic -------------------------------------------------------------
    console.print("\n[bold]AI REVIEW[/bold]\n")

    ai_result = None
    unconfirmed = []
    if settings.ai.enabled:
        with console.status("Running independent AI review (Gemini) ..."):
            context = gather_evidence_context(diff, results, settings.task.description)
            ai_result = run_ai_review(context)
            unconfirmed = get_unconfirmed_findings(ai_result)
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

    # -- Verdict ---------------------------------------------------------------
    console.print("\n----------------------------------------------\n")

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
        console.print("[bold]CONFIRMED[/bold]\n")
        for f in confirmed:
            loc = f"  {f.file}:{f.line}" if f.file else ""
            console.print(f"  [red]{f.title}[/red]{loc}")
            console.print(f"     Detected by {f.source}\n")

    if unconfirmed:
        console.print("[bold]UNCONFIRMED (AI)[/bold]\n")
        for f in unconfirmed:
            loc = f"  {f.file}:{f.line}" if f.file else ""
            console.print(f"  [yellow]{f.title}[/yellow]{loc}")
            if f.recommendation:
                console.print(f"     {f.recommendation}")
            console.print()

    console.print("----------------------------------------------\n")

    # -- Reports ---------------------------------------------------------------
    report = VerificationReport(
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
        metadata={"diff_text": diff.diff_text}
    )

    os.makedirs(".sentinel", exist_ok=True)
    generate_markdown_report(report, ".sentinel/report.md")
    generate_json_report(report, ".sentinel/report.json")

    console.print("Reports:")
    console.print("  .sentinel/report.md")
    console.print("  .sentinel/report.json")
    console.print("\nRun [bold]sentinel ui[/bold] to open the verification dashboard.\n")


@app.command()
def declare():
    """Generate an AI Use Declaration from the latest verification report."""

    report_path = Path(".sentinel/report.json")
    if not report_path.exists():
        console.print("[bold red]Error:[/bold red] No verification report found. Run [bold]sentinel verify[/bold] first.")
        raise typer.Exit(1)

    with open(report_path, "r") as f:
        data = json.load(f)

    checks = [c["name"] for c in data.get("checks", [])]
    provider = data.get("ai_provider", "Gemini")
    if not provider:
        provider = "Gemini"

    declaration = f"""# AI Use Declaration

## Project
{data.get("repository", "unknown")}

## Verification Run
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
    """Open a local verification dashboard in the browser."""

    report_path = Path(".sentinel/report.json")
    if not report_path.exists():
        console.print("[bold red]Error:[/bold red] No verification report found. Run [bold]sentinel verify[/bold] first.")
        raise typer.Exit(1)

    with open(report_path, "r") as f:
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
    console.print(f"Sentinel dashboard running at [bold cyan]{url}[/bold cyan]")
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

    with open(report_path, "r") as f:
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
        console.print(f"{idx}. Gemini identified a possible {f.get('title').lower()}. This is [yellow]UNCONFIRMED[/yellow].")
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
