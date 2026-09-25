# SENTINEL-X Changelog

All notable changes to this project are documented in this file.

## [2.0.0] - SENTINEL-X Evolution

### Added
- **Unified Event & Trace Model (`sentinel/events/`)**: Introduced `run_id` and structured span logging with JSONL persistence.
- **ToolShield Security & Policy Engine (`sentinel/shield/`)**: Explicit tool registry with `verified`, `trusted`, `unknown`, `blocked` trust levels, deterministic permission evaluation (`ALLOW`, `DENY`, `REVIEW`), and argument injection defense.
- **MCP Gateway Foundation (`sentinel/mcp/`)**: Model Context Protocol integration layer supporting tool discovery, registration, input schema validation, and safe execution.
- **Output Sanitization (`sentinel/sanitizer/`)**: Zero-loss regex interceptor detecting and redacting database connection credentials, API keys, private keys, bearer tokens, and PII.
- **Agent Execution Reliability (`sentinel/reliability/`)**: ExecutionManager tracking execution states (`PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `TIMED_OUT`, `CANCELLED`, `RETRYING`), retries with backoff, and duplicate protection via idempotency keys.
- **Checkpoint & Recovery (`sentinel/reliability/checkpoint.py`)**: State snapshotting enabling seamless task recovery without rerunning completed side effects.
- **Deterministic Evaluation Engine (`sentinel/eval/`)**: Benchmark suite scoring task success, safety, tool selection, and argument correctness.
- **Red Team Security Corpus (`sentinel/eval/redteam.py`)**: Automated test dataset covering prompt injection, tool manipulation, path traversal, and secret leakage.
- **Cost & Latency Telemetry (`sentinel/metrics/`)**: Standardized pricing adapters for Gemini, OpenAI, Claude, and local models.
- **Model Router (`sentinel/ai/router.py`)**: Deterministic task-to-model routing across `cheap`, `standard`, and `reasoning` tiers.
- **Interactive Control Plane UI (`sentinel/ui/`, `web-demo/`)**: Upgraded web dashboard featuring Overview, Event Timeline, ToolShield Decisions, Evaluation Scorecard, and Cost Telemetry.
- **VS Code Extension Upgrades (`vscode-extension/`)**: Enhanced sidebar view with telemetry, ToolShield status, and diagnostics.
- **GitHub Actions CI/CD Gate (`.github/workflows/sentinel.yml`)**: Automated verification and security gating in pull requests.
- **End-to-End Demo (`demo/sentinel-x-agent/`)**: Autonomous agent execution scenario demonstrating attack prevention and telemetry.

### Changed
- Extended `VerificationReport` schema with backward-compatible telemetry, tool decisions, and trace events.
- Upgraded CLI commands (`verify`, `declare`, `ui`, `explain`, `eval`, `redteam`, `trace`, `demo-agent`).

---

## [1.0.0] - SENTINEL Initial Release
- Deterministic verification engine (pytest, semgrep, gitleaks, ruff, mypy, pip-audit).
- Gemini AI Critic code review.
- CONFIRMED vs UNCONFIRMED evidence classification.
- VS Code extension and live web demo.
