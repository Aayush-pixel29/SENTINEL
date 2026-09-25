# SENTINEL-X Architecture Specification

## 1. Executive Overview

**SENTINEL-X** is an open-source AI Agent Reliability, Security & Verification Control Plane. It evolves the core philosophy of SENTINEL (*AI writes → SENTINEL verifies → Human decides*) into a comprehensive control plane governing autonomous and semi-autonomous AI agents, tool execution, security boundaries, deterministic evaluations, cost/latency telemetry, and CI/CD quality gates.

The system ensures that **no AI model's unverified assertion is ever treated as deterministic proof**, explicitly separating **CONFIRMED** (deterministic evidence) from **UNCONFIRMED** (probabilistic AI critic / agent hypotheses).

---

## 2. Current Architecture (SENTINEL v1.0)

### 2.1 Component Structure
```text
sentinel/
├── __init__.py
├── models.py              # VerificationReport, Finding, CheckResult, Verdict, Classification
├── config.py              # YAML config loader (.sentinel/config.yml)
├── cli.py                 # Typer CLI (verify, declare, ui, explain)
├── git/
│   └── diff.py            # Git status, branch, commit, unified diff inspection
├── checks/                # Deterministic check runners
│   ├── base.py            # BaseCheck abstraction
│   ├── tests.py           # Pytest runner
│   ├── lint.py            # Ruff linter runner
│   ├── typecheck.py       # Mypy typechecker runner
│   ├── semgrep.py         # Semgrep static analysis runner
│   ├── secrets.py         # Gitleaks secret scanner runner
│   └── dependencies.py    # Pip-audit CVE dependency scanner
├── engine/
│   ├── evidence.py        # Finding classification & evidence formatting
│   └── verdict.py         # Deterministic priority engine (BLOCKED > INCOMPLETE > REVIEW > VERIFIED)
├── ai/
│   ├── prompts.py         # System prompt for independent Gemini critic
│   └── critic.py          # Google GenAI SDK integration with structured JSON schema
├── report/
│   ├── json.py            # .sentinel/report.json generator
│   └── markdown.py        # .sentinel/report.md generator
└── ui/
    └── template.py        # Self-contained dark-mode dashboard generator
```

### 2.2 Current Data Flow
```text
Developer / AI modifies code in Git workspace
                  │
                  ▼
         `sentinel verify`
                  │
                  ├── Git Inspection (diff, branch, commit)
                  ├── Deterministic Checks (pytest, ruff, mypy, semgrep, gitleaks, pip-audit)
                  │         └── Categorized as CONFIRMED findings
                  ├── AI Critic Review (Gemini 2.5 Flash with structured schema)
                  │         └── Categorized as UNCONFIRMED findings
                  └── Verdict Engine
                            │
                            ▼
          Report Generation (.sentinel/report.json, .sentinel/report.md)
                            │
                            ├── `sentinel ui` (Local HTTP Server)
                            ├── `sentinel explain` (CLI Explainer)
                            └── VS Code Extension / CI Quality Gate
```

### 2.3 VS Code Extension & Web Demo Relationship
* **VS Code Extension (`vscode-extension/`)**:
  - Invokes `sentinel verify` via `child_process.spawn`.
  - Reads `.sentinel/report.json`.
  - Emits in-editor diagnostic markers (red squiggles for `CONFIRMED` high/critical issues, yellow squiggles for `UNCONFIRMED` AI issues).
  - Provides a Webview Sidebar Panel for viewing checks, findings, and clicking to jump to line numbers.
* **Web Demo (`web-demo/`)**:
  - Standalone static HTML/JS viewer consuming sample report JSON payloads (`data.js`) demonstrating vulnerable vs verified scenarios.

---

## 3. SENTINEL-X Target Architecture

SENTINEL-X expands the verification boundary from static code diffs to active agent workflows, tool invocations, and runtime execution safety:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        AI AGENT WORKFLOW                               │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        SENTINEL-X CONTROL PLANE                        │
│                                                                        │
│  ┌───────────────────────┐  ┌───────────────────────────────────────┐  │
│  │ Unified Event Trace   │  │ ToolShield Policy Engine              │  │
│  │ (Run ID, Spans, JSONL)│  │ (Registry, Allow/Deny/Review, Schema) │  │
│  └───────────────────────┘  └───────────────────────────────────────┘  │
│  ┌───────────────────────┐  ┌───────────────────────────────────────┐  │
│  │ Execution Reliability │  │ Output Sanitizer                      │  │
│  │ (Idempotency, Retries)│  │ (Secrets, PII, Credentials, Leaks)    │  │
│  └───────────────────────┘  └───────────────────────────────────────┘  │
│  ┌───────────────────────┐  ┌───────────────────────────────────────┐  │
│  │ Checkpoint & Recovery │  │ Deterministic Evaluation Runner       │  │
│  │ (Step State & Resume) │  │ (Task, Safety, Groundedness, Success) │  │
│  └───────────────────────┘  └───────────────────────────────────────┘  │
│  ┌───────────────────────┐  ┌───────────────────────────────────────┐  │
│  │ Model Router & Pricing│  │ Code & Security Verification Engine   │  │
│  │ (Cost / Latency Track)│  │ (Tests, Semgrep, Gitleaks, AI Critic) │  │
│  └───────────────────────┘  └───────────────────────────────────────┘  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 UNIFIED EVIDENCE & TELEMETRY REPORT                    │
│   (Run Trace, Tool Decisions, Code Verdict, Eval Metrics, Cost/Time)   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     HUMAN DECISION & QUALITY GATES                     │
│    (VS Code Extension, Web Dashboard, CI/CD Gate, AI Use Decl)         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Architectural Subsystems

### 4.1 Unified Event & Trace Model (`sentinel/events/`)
- Every execution run receives a unique `run_id` (e.g. `run_2026_09_25_a1b2c3d4`).
- Granular event spans record: `run_id`, `event_id`, `parent_event_id`, `event_type`, `component`, `status`, `started_at`, `duration_ms`, `input_tokens`, `output_tokens`, `metadata`, `error`.
- Stored locally via structured JSONL append-log (`.sentinel/events/<run_id>.jsonl`) and indexed for zero-dependency local operation.

### 4.2 ToolShield Security & Policy Engine (`sentinel/shield/`)
- **Explicit Tool Registry**: Every tool is registered with strict metadata: name, version, trust level (`verified`, `trusted`, `unknown`, `blocked`), risk level (`low`, `medium`, `high`, `critical`), allowed operations, schema constraints, and authentication requirements.
- **Policy Engine**: Enforces deterministic evaluation pipelines:
  `Tool Request → Identity → Permission → Schema → Risk → Trust → Approval Requirement → Decision (ALLOW / DENY / REVIEW)`
- **MCP Gateway (`sentinel/mcp/`)**: Intercepts Model Context Protocol tool requests, introspects tool schemas, validates inputs, and ensures MCP tools adhere to ToolShield policies.

### 4.3 Tool Output Sanitizer (`sentinel/sanitizer/`)
- Intercepts all raw outputs before they return to agent context or logs.
- Detects and redacts credentials (connection strings, bearer tokens, API keys, private keys), sensitive PII (emails, SSNs), sensitive internal endpoints, and overly verbose stack traces.
- Produces auditable metadata: `{ "sanitized": true, "redactions": n, "categories": [...] }`.

### 4.4 Agent Execution Reliability & Checkpoints (`sentinel/reliability/`)
- **Execution Manager**: Tracks execution states (`PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `TIMED_OUT`, `CANCELLED`, `RETRYING`), enforces timeouts, handles retry backoff, and provides idempotency protection against duplicate execution IDs.
- **Checkpoint / Recovery**: Captures lightweight state snapshots (`checkpoint_id`, `run_id`, `state`, `completed_steps`, `failed_step`, `resume_from`) allowing paused or failed runs to resume without re-running irreversible side effects.

### 4.5 Evaluation & Red Team Engine (`sentinel/eval/`)
- Deterministic benchmark suite evaluating agent behavior across standard dimensions: `task_success`, `tool_selection`, `tool_argument_correctness`, `structured_output_validity`, `safety`, `groundedness`, `latency`, `cost`.
- Red team test harness simulating prompt injections, tool description manipulations, path traversals, credential harvesting, and instruction overrides against mock environments.

### 4.6 Cost, Latency & Model Routing (`sentinel/metrics/`, `sentinel/ai/router.py`)
- Pricing adapter normalizing token usage and calculating estimated costs across providers (Google Gemini, OpenAI, Anthropic, Local).
- Rule-based model router directing tasks to `cheap`, `standard`, or `reasoning` tiers based on cost constraints, latency limits, and task criticality.

---

## 5. Compatibility Constraints & Invariants

1. **Zero Breaking Changes to Existing CLI**: `sentinel verify`, `sentinel declare`, `sentinel ui`, `sentinel explain` must continue working exactly as before.
2. **Backward-Compatible Report Format**: Old consumers of `.sentinel/report.json` must find all existing fields (`verdict`, `checks`, `confirmed_findings`, `unconfirmed_findings`, `repository`, `branch`, `commit`, `metadata`) intact.
3. **Local-First & Offline Resilience**: No external cloud database required. All traces and state are stored in lightweight local files (`.sentinel/`).
4. **Deterministic Separation**: AI opinions remain strictly labeled `UNCONFIRMED`.
