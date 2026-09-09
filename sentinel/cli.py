import typer
from rich.console import Console

app = typer.Typer(help="Sentinel - AI Code Verification Layer")
console = Console()

import json
import os
from pathlib import Path
from sentinel.config import load_config
from sentinel.git.diff import get_git_diff
from sentinel.checks.tests import PytestCheck
from sentinel.checks.lint import RuffCheck
from sentinel.checks.typecheck import MypyCheck
from sentinel.checks.semgrep import SemgrepCheck
from sentinel.checks.secrets import GitleaksCheck
from sentinel.checks.dependencies import PipAuditCheck
from sentinel.engine.evidence import get_confirmed_findings, get_unconfirmed_findings, gather_evidence_context
from sentinel.engine.verdict import determine_verdict
from sentinel.ai.critic import run_ai_review
from sentinel.models import VerificationReport
from sentinel.report.markdown import generate_markdown_report
from sentinel.report.json import generate_json_report

app = typer.Typer(help="Sentinel - AI Code Verification Layer")
console = Console()

@app.command()
def verify(config: str = typer.Option(".sentinel/config.yml", help="Path to config file")):
    """
    Run Sentinel verification pipeline.
    """
    console.print(r"""[bold cyan]
╭──────────────────────────────────────────────╮
│                 SENTINEL                     │
│       AI Code Verification                   │
╰──────────────────────────────────────────────╯
[/bold cyan]""")
    
    settings = load_config(config)
    
    console.print("Analyzing Git changes...")
    try:
        diff = get_git_diff()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red]\n{e}")
        raise typer.Exit(1)
        
    console.print(f"\n[bold]CHANGE[/bold]")
    console.print(f"  Files changed     {diff.files_changed}")
    console.print(f"  Lines added       {diff.lines_added}")
    console.print(f"  Lines removed     {diff.lines_removed}")

    console.print("\n[bold]DETERMINISTIC CHECKS[/bold]\n")
    
    # Initialize configured checks
    check_runners = []
    if settings.checks.test.enabled: check_runners.append(PytestCheck())
    if settings.checks.lint.enabled: check_runners.append(RuffCheck())
    if settings.checks.typecheck.enabled: check_runners.append(MypyCheck())
    if settings.checks.semgrep.enabled: check_runners.append(SemgrepCheck())
    if settings.checks.secrets.enabled: check_runners.append(GitleaksCheck())
    if settings.checks.dependencies.enabled: check_runners.append(PipAuditCheck())

    results = []
    for runner in check_runners:
        with console.status(f"Running {runner.name}...") as status:
            res = runner.run()
            results.append(res)
            icon = "✓" if res.status == "PASSED" else "✗" if res.status == "FAILED" else "⚪"
            summary_text = f"passed" if res.status == "PASSED" else f"{len(res.findings)} finding(s)" if res.findings else res.status.value
            console.print(f"  {icon} {runner.name.ljust(18)} {summary_text}")
            
    confirmed = get_confirmed_findings(results)
    
    console.print("\n[bold]AI CRITIC[/bold]\n")
    
    ai_result = None
    if settings.ai.enabled:
        with console.status("Running independent AI review...") as status:
            context = gather_evidence_context(diff, results, settings.task.description)
            ai_result = run_ai_review(context)
            unconfirmed = get_unconfirmed_findings(ai_result)
            if ai_result.status == "PASSED":
                if unconfirmed:
                    console.print(f"  ⚠ {len(unconfirmed)} unconfirmed concern(s)")
                else:
                    console.print("  ✓ No concerns raised")
            else:
                 console.print(f"  ⚪ AI review unavailable: {ai_result.summary}")
    else:
        unconfirmed = []
        console.print("  ⚪ AI review disabled")

    console.print("\n──────────────────────────────────────────────\n")
    
    verdict = determine_verdict(results, confirmed, unconfirmed, ai_result.status if ai_result else "SKIPPED")
    
    console.print("[bold]VERDICT[/bold]\n")
    if verdict == "BLOCKED":
        console.print("  [bold red]🔴 BLOCKED[/bold red]\n")
    elif verdict == "REVIEW":
        console.print("  [bold yellow]🟡 REVIEW[/bold yellow]\n")
    elif verdict == "INCOMPLETE":
        console.print("  [bold white]⚪ INCOMPLETE[/bold white]\n")
    else:
        console.print("  [bold green]🟢 VERIFIED[/bold green]\n")

    if confirmed:
        console.print("[bold]CONFIRMED[/bold]\n")
        for f in confirmed:
            console.print(f"  [red]🔴 {f.title}[/red]")
            if f.file:
                console.print(f"     {f.file}:{f.line if f.line else ''}")
            console.print(f"     Detected by {f.source}\n")

    if unconfirmed:
        console.print("[bold]UNCONFIRMED[/bold]\n")
        for f in unconfirmed:
            console.print(f"  [yellow]🟡 {f.title}[/yellow]")
            if f.file:
                console.print(f"     {f.file}:{f.line if f.line else ''}")
            console.print("")

    console.print("──────────────────────────────────────────────\n")
    
    # Generate reports
    report = VerificationReport(
        verdict=verdict,
        changed_files=diff.changed_files_list,
        checks=results,
        confirmed_findings=confirmed,
        unconfirmed_findings=unconfirmed,
        ai_review=ai_result.model_dump() if ai_result else {"summary": "Disabled"}
    )
    
    generate_markdown_report(report, ".sentinel/report.md")
    generate_json_report(report, ".sentinel/report.json")
    
    console.print("Reports:")
    console.print("  .sentinel/report.md")
    console.print("  .sentinel/report.json\n")


@app.command()
def declare():
    """
    Generate an AI Use Declaration.
    """
    console.print("Generating AI Use Declaration...")
    
    report_path = Path(".sentinel/report.json")
    if not report_path.exists():
        console.print("[bold red]Error:[/bold red] No verification report found. Run `sentinel verify` first.")
        raise typer.Exit(1)
        
    with open(report_path, "r") as f:
        data = json.load(f)
        
    checks = [c["name"] for c in data.get("checks", [])]
    
    declaration = f"""# AI Use Declaration

## AI Tools Used
- Claude 3.5 Sonnet

## AI-Assisted Work
- Code review
- Potential issue identification
- Security and edge case reasoning

## Automated Verification (Deterministic)
{chr(10).join([f"- {c}" for c in checks])}

## Human Verification
The developer reviewed the generated findings,
validated changes, and made the final decision
about whether the software was ready to submit.

## Limitations
AI findings are not treated as proof.
Deterministic findings are reported separately.
A clean report does not guarantee completely
secure software.
"""
    with open("AI_USE_DECLARATION.md", "w", encoding="utf-8") as f:
        f.write(declaration)
        
    console.print("Created [bold]AI_USE_DECLARATION.md[/bold]")

def main():
    app()

if __name__ == "__main__":
    main()
