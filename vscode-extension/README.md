# Sentinel VS Code Extension

Sentinel brings the existing Sentinel verification engine into VS Code.

## Developer experience

1. Install this extension.
2. Open any Git repository.
3. Run **Sentinel: Setup Verification Engine** once if the CLI is not installed.
4. Click the Sentinel shield in the Activity Bar.
5. Click **Verify Changes**.

The extension runs the existing `sentinel verify` CLI in the current workspace. It then reads `.sentinel/report.json` and presents the verdict, checks, findings, and explanations inside VS Code.

## Architecture

```text
VS Code
  ↓
Sentinel Extension
  ↓
sentinel verify
  ↓
Git diff + pytest + Ruff + mypy + Semgrep + Gitleaks + pip-audit + Gemini
  ↓
.sentinel/report.json
  ↓
Sentinel sidebar + VS Code diagnostics
```

The extension is intentionally thin: the Python verification engine remains the source of truth.

## Install from source during the hackathon

Open this folder in VS Code and press `F5` to launch an Extension Development Host.

For packaging, install `@vscode/vsce` and run `vsce package`.

## CLI requirement

The extension expects the Sentinel Python CLI to be available as `sentinel`. It also falls back to `python -m sentinel.cli verify` when the command is not found.

For a developer using the published GitHub repository:

```bash
python -m pip install -e .
```

Then open their own repository in VS Code and run Sentinel from the Sentinel sidebar.

## Current scope

- One-click verification
- Verdict in the Activity Bar
- Check status
- Confirmed vs unconfirmed findings
- Click a finding to jump to its file/line
- Explain verdict
- Optional verify-on-save
- No source-code upload service
- No database
