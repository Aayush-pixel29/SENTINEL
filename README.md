# Sentinel

**Sentinel is an open-source, local-first verification layer for AI-generated code.**

> **AI writes the code. Sentinel verifies what can actually be verified.**

---

## 1. What Sentinel Is

Sentinel is a verification layer that sits between your AI coding agent and your Git repository. It orchestrates a suite of deterministic engineering and security checks alongside an independent AI critic to produce an auditable, evidence-driven verification report.

## 2. Why AI-generated code needs verification

AI coding agents (Claude Code, Gemini, Cursor, Copilot, Codex) can generate code changes in seconds. But *verifying* that change is still expensive. When an AI says "Done. Tests are passing.", the developer has to ask:
- What actually changed?
- Did it introduce a security problem?
- Did it expose a secret?
- Did it change dependencies dangerously?
- Can I trust this change enough to merge?

**The cost of generating code is falling faster than the cost of trusting it.**

## 3. How it works

```text
AI writes
    ↓
Sentinel verifies
    ↓
Human decides
```

Sentinel operates directly on your local Git repository. It reads the Git diff, runs deterministic checks, sends the diff to an AI critic, and surfaces the evidence natively in your IDE (VS Code).

## 4. Installation

**1. Install the Verification Engine (CLI)**
```bash
git clone https://github.com/Aayush-pixel29/SENTINEL.git
cd SENTINEL
pip install -e .
```

**2. Configure AI (First time only)**
```bash
export GEMINI_API_KEY="your_key_here"     # macOS/Linux
$env:GEMINI_API_KEY="your_key_here"       # PowerShell
```

**3. Install the VS Code Extension**
- Open the `vscode-extension` directory in VS Code.
- Press `F5` to launch the Extension Development Host.

## 5. VS Code Workflow (Primary Experience)

Sentinel is designed to live where you work. 
1. Open your project in VS Code.
2. Let your AI agent (Cursor, Copilot, etc.) make changes.
3. Click the 🛡 **Sentinel** icon in the Activity Bar.
4. Click **Verify Changes**.
5. Review the evidence directly in the sidebar, and click findings to jump to the exact file and line in the editor.

## 6. CLI Workflow (Headless Engine)

The VS Code extension is powered by the Sentinel CLI engine. You can also run it directly:

```bash
cd your-project
sentinel verify
```
This generates `.sentinel/report.json`. You can then view the results in the terminal, or launch the standalone browser UI:
```bash
sentinel ui
```

## 7. Verification Architecture

```text
                 SENTINEL
                    │
        ┌───────────┴───────────┐
        │                       │
   VS CODE EXTENSION        CLI / ENGINE
        │                       │
        └───────────┬───────────┘
                    │
                Git Diff
                    │
       ┌────────────┼────────────┐
       ↓            ↓            ↓
    Testing      Security      AI Critic
    (pytest)     (semgrep,     (Gemini)
                 gitleaks)       │
       │            │            │
       └────────────┼────────────┘
                    ↓
             Evidence Engine
                    ↓
          .sentinel/report.json
```

## 8. CONFIRMED vs UNCONFIRMED

Sentinel strictly separates deterministic tool output from AI reasoning:

| AI Opinion | Sentinel Evidence |
|---|---|
| "This looks secure." | Semgrep detected SQL injection at `app.py:28` |
| Not proof | **Deterministic fact** |

- **CONFIRMED**: A deterministic tool (e.g., Semgrep, pytest) produced a finding.
- **UNCONFIRMED (AI)**: The AI Critic raised a concern requiring human verification. We never say "AI found a vulnerability." We say "AI raised a concern."

## 9. Verdicts

Sentinel assigns one of four verdicts to your changes:
- **VERIFIED**: Required checks passed. No significant confirmed findings remain. Human review is still recommended.
- **REVIEW**: No confirmed blocker, but human attention is required (e.g., an unconfirmed AI concern).
- **BLOCKED**: Sentinel found confirmed blocking evidence or failing required checks.
- **INCOMPLETE**: Sentinel could not complete all required verification checks.

## 10. Responsible AI

- Sentinel does **not** execute AI-generated exploit payloads.
- Sentinel does **not** claim AI-generated software is safe because an AI said so.
- A clean report does **not** guarantee completely secure software.
- AI findings are clearly labelled **UNCONFIRMED**.
- No API keys are stored in reports, logs, or terminal output.

## 11. Demo

To test Sentinel, use the provided demo project:
1. Open the repository in VS Code.
2. Launch the extension (`F5`).
3. Open the `demo/vulnerable-fastapi` folder in the Extension Host.
4. Run `Sentinel: Verify Changes` via the sidebar.
5. Observe the **BLOCKED** verdict and the **CONFIRMED** SQL injection finding.
6. Fix the vulnerability and verify again to achieve **VERIFIED**.

## 12. Roadmap

- **Phase 1**: Local Sentinel engine + CLI + VS Code Extension (✅ NOW)
- **Phase 2**: GitHub Actions / Pull Request verification
- **Phase 3**: GitHub PR comments/checks
- **Phase 4**: JetBrains integration

---
**License**: MIT
