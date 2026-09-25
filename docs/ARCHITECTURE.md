# SENTINEL-X Architecture Specification

## 1. Executive Overview

**SENTINEL-X** is an open-source AI Agent Reliability, Security & Verification Control Plane. It evolves the core philosophy of SENTINEL (*AI writes → SENTINEL-X verifies → Human decides*) into a comprehensive control plane governing autonomous and semi-autonomous AI agents, tool execution, security boundaries, deterministic evaluations, cost/latency telemetry, and CI/CD quality gates.

The system ensures that **no AI model's unverified assertion is ever treated as deterministic proof**, explicitly separating **CONFIRMED** (deterministic evidence) from **UNCONFIRMED** (probabilistic AI critic / agent hypotheses).

---

## 2. Subsystem Architecture

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
│  │ Model Routing Abstract│  │ Code & Security Verification Engine   │  │
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

## 3. Subsystem Breakdown

### 3.1 Unified Event & Trace Model (`sentinel/events/`)
- Every execution run receives a unique `run_id` (e.g. `run_2026_09_25_a1b2c3d4`).
- Granular event spans record: `run_id`, `event_id`, `parent_event_id`, `event_type`, `component`, `status`, `started_at`, `duration_ms`, `input_tokens`, `output_tokens`, `metadata`, `error`.
- Stored locally via structured JSONL append-logs (`.sentinel/events/<run_id>.jsonl`) for zero-dependency local operation.

### 3.2 ToolShield Security & Policy Engine (`sentinel/shield/`)
- **Explicit Tool Registry**: Every tool is registered with strict metadata: name, version, trust level (`verified`, `trusted`, `unknown`, `blocked`), risk level (`low`, `medium`, `high`, `critical`), allowed operations, schema constraints, and authentication requirements.
- **Policy Engine**: Enforces deterministic evaluation pipelines:
  `Tool Request → Identity → Permission → Schema → Risk → Trust → Approval Requirement → Decision (ALLOW / DENY / REVIEW)`
- **MCP-Compatible Tool Gateway (`sentinel/mcp/`)**: Registers MCP-shaped tool schemas, validates inputs, and binds local Python handlers under ToolShield governance with output sanitization and telemetry logging. *(Note: This gateway operates as a local tool adapter rather than a full remote JSON-RPC transport client).*

### 3.3 Tool Output Sanitizer (`sentinel/sanitizer/`)
- Intercepts all raw outputs before they return to agent context or logs.
- Detects and redacts credentials (connection strings, bearer tokens, API keys, private keys), sensitive PII (emails, SSNs), and sensitive endpoints.
- Produces auditable metadata: `{ "sanitized": true, "redactions": n, "categories": [...] }`.

### 3.4 Agent Execution Reliability & Checkpoints (`sentinel/reliability/`)
- **Execution Manager**: Tracks execution states (`PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `TIMED_OUT`, `CANCELLED`, `RETRYING`), enforces timeouts, handles retry backoff, and provides idempotency protection against duplicate execution IDs.
- **Checkpoint / Recovery**: Captures lightweight state snapshots (`checkpoint_id`, `run_id`, `state`, `completed_steps`, `failed_step`, `resume_from`) allowing paused or failed runs to resume without re-running irreversible side effects.

### 3.5 Evaluation & Red Team Engine (`sentinel/eval/`)
- Deterministic benchmark suite evaluating agent behavior across standard dimensions: `task_success`, `tool_selection`, `tool_argument_correctness`, `structured_output_validity`, `safety`, `groundedness`, `latency`, `cost`.
- Red team test harness simulating prompt injections, tool description manipulations, path traversals, credential harvesting, and instruction overrides against mock environments (6/6 test cases mitigated in default suite).

### 3.6 Cost, Latency & Model Routing (`sentinel/metrics/`, `sentinel/ai/router.py`)
- Pricing adapter normalizing token usage and calculating estimated costs across providers (Google Gemini, OpenAI, Anthropic, Local).
- **Model Router Abstraction**: Rule-based model router directing tasks to `cheap`, `standard`, or `reasoning` tiers based on cost constraints, latency limits, and task criticality. *(Note: This component provides deterministic tier selection and fallback chains rather than dynamic runtime execution optimization).*

---

## 4. Invariants & Compatibility

1. **Zero Regressions on Existing Commands**: `sentinel verify`, `sentinel declare`, `sentinel ui`, `sentinel explain` operate identically with enhanced telemetry.
2. **Backward-Compatible Report Format**: Consumers of `.sentinel/report.json` find all legacy fields (`verdict`, `checks`, `confirmed_findings`, `unconfirmed_findings`) preserved alongside new telemetry.
3. **Local-First & Offline Resilience**: No external cloud database required.
4. **Deterministic Separation**: AI opinions remain strictly labeled `UNCONFIRMED`.
