# Sentinel

> **AI writes the code. Sentinel verifies what can actually be verified.**

Evidence-driven verification for AI-generated code.

**Challenge:** Developer Productivity  
**Category:** Understand + Test + Review + Ship

---

## The Problem

AI coding agents (Claude Code, Gemini, Cursor, Copilot, Codex) can generate a code change in seconds.

But *verifying* that change is still expensive. When an AI says "Done. Tests are passing.", the developer has to ask:

- What actually changed?
- Did the tests pass?
- Did it break typing / linting?
- Did it introduce a security problem?
- Did it expose a secret?
- Did it change dependencies dangerously?
- Can I trust this change enough to merge?

**The cost of generating code is falling faster than the cost of trusting it.**

## The Solution

Sentinel answers all of those questions in **one verification step**.

```
AI coding agent
      |
   code change
      |
   SENTINEL
      |-- Git diff analysis
      |-- Tests (pytest)
      |-- Lint (ruff)
      |-- Type checking (mypy)
      |-- Security analysis (Semgrep)
      |-- Secret detection (Gitleaks)
      |-- Dependency audit (pip-audit)
      |-- Independent AI reasoning (Gemini)
      |
   Evidence synthesis
      |
   BLOCKED / INCOMPLETE / REVIEW / VERIFIED
      |
   Human decides
```

## Why Sentinel Is Different

| AI opinion | Sentinel evidence |
|---|---|
| "This looks secure." | Semgrep detected SQL injection at `app/api.py:28` |
| Not proof | **Deterministic fact** |

Sentinel separates:

- **CONFIRMED** -- a deterministic tool produced a finding (fact)
- **UNCONFIRMED** -- AI raised a concern requiring human verification (reasoning)

We never say "AI found a vulnerability." We say "AI raised a concern."

## Installation

```bash
git clone https://github.com/Aayush-pixel29/SENTINEL.git
cd SENTINEL
pip install -e .
```

Set your Gemini API key:
```bash
export GEMINI_API_KEY="your_key_here"     # macOS/Linux
$env:GEMINI_API_KEY="your_key_here"       # PowerShell
```

## Configuration

Create `.sentinel/config.yml` in your project root:

```yaml
project:
  name: my-app
  language: python
  framework: fastapi

task:
  description: "Add a user profile lookup endpoint."

checks:
  test:
    enabled: true
    command: "pytest"
  lint:
    enabled: true
    command: "ruff check ."
  typecheck:
    enabled: true
    command: "mypy ."
  semgrep:
    enabled: true
  secrets:
    enabled: true
  dependencies:
    enabled: true

ai:
  enabled: true
```

## Usage

### Verify your changes
```bash
sentinel verify
```

### Open the local dashboard
```bash
sentinel ui
```

### Generate an AI use declaration
```bash
sentinel declare
```

## Example Flow

```
$ sentinel verify

----------------------------------------------
              S E N T I N E L
     Evidence-driven code verification
----------------------------------------------

  Repository   SENTINEL
  Branch       main
  Commit       a84c2d1

Analyzing Git changes ...

CHANGE  (staged)
  Files changed     3
  Lines added       +87
  Lines removed     -14

DETERMINISTIC CHECKS

  pytest           PASS
  ruff             PASS
  mypy             PASS
  semgrep          FAIL  1 finding(s)
  gitleaks         PASS
  pip-audit        PASS

AI REVIEW

  1 unconfirmed concern(s)

----------------------------------------------

VERDICT

  BLOCKED

CONFIRMED

  SQL Injection  demo/vulnerable-fastapi/main.py:28
     Detected by semgrep

UNCONFIRMED (AI)

  Authorization boundary may be incomplete
     demo/vulnerable-fastapi/main.py:28
```

## Security & Responsible AI

- Sentinel does **not** execute AI-generated exploit payloads.
- Sentinel does **not** claim AI-generated software is safe because an AI said so.
- Deterministic findings are reported separately from AI suspicions.
- AI findings are labelled **UNCONFIRMED** and require human verification.
- A clean report does **not** guarantee completely secure software.
- No API keys are stored in reports, logs, or terminal output.

## Limitations

- AI findings can be wrong (they are reasoning, not proof)
- Scanners have coverage limitations
- Only configured checks are executed
- AI provider availability affects AI review
- No guarantee of absolute security

## Roadmap

- GitHub Action integration
- VS Code extension
- JavaScript/TypeScript, Go, Rust, Java support
- Multiple AI providers
- Verification history
- CI policy enforcement
- Agent/MCP security analysis

## License

MIT
