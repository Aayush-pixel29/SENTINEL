# SENTINEL-X VS Code Extension

**AI Agent Reliability, Security & Verification Control Plane, directly inside VS Code.**

SENTINEL-X embeds the verification engine, ToolShield security policies, event timeline, deterministic findings, and token/latency telemetry directly into your IDE.

---

## Developer Experience

1. Open any Git repository workspace in VS Code.
2. If using for the first time, click **Sentinel-X: Setup Engine** or run `pip install -e .` in your terminal.
3. Click the 🛡 **Sentinel-X** icon in the Activity Bar.
4. Click **Verify Changes**.
5. The extension runs the local Python verification engine (`sentinel verify --eval`), loads `.sentinel/report.json`, and updates:
   - In-editor diagnostic squiggles (red for confirmed critical bugs/vulnerabilities, yellow for unconfirmed AI concerns).
   - Sidebar verdict badge, deterministic check results, ToolShield decisions, and LLM telemetry.
   - Click any finding in the sidebar to jump directly to the exact file and line in the editor.

---

## Architecture

```text
VS Code (Activity Bar & Diagnostics)
  │
  ▼
SENTINEL-X Extension (`extension.js`)
  │
  ▼
`sentinel verify --eval` (Python Engine)
  │
  ├── Git Inspection (diff, branch, commit)
  ├── Deterministic Checks (Pytest, Semgrep, Gitleaks, Pip-audit, Ruff, Mypy)
  ├── ToolShield Security & Policy Engine
  ├── Independent AI Critic (Gemini)
  └── Telemetry & Cost Accounting
  │
  ▼
`.sentinel/report.json`
  │
  ▼
Sidebar Webview & In-Editor Diagnostics
```

---

## Extension Commands

- `Sentinel-X: Verify Changes` (`sentinel.verify`)
- `Sentinel-X: Explain Verdict` (`sentinel.explain`)
- `Sentinel-X: Open Verification Report` (`sentinel.openReport`)
- `Sentinel-X: Setup Engine` (`sentinel.setup`)

---

## License

MIT License. See repository `LICENSE` for details.
