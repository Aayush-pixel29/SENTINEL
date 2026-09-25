# SENTINEL-X End-to-End Agent Execution Demo

This demo illustrates the autonomous agent security control plane in action.

## What this demo demonstrates:

1. **Adversarial Tool Blockade**: The mock agent attempts to invoke `raw_bash_exec` with an exploit payload. ToolShield intercepts and blocks the call (`DENY`).
2. **Path Traversal Defense**: The agent attempts to read `../../../../etc/passwd`. ToolShield detects argument evasion and blocks execution.
3. **Legitimate Execution & Output Sanitization**: The agent invokes `read_repository`. The raw output contains sensitive database credentials and PII. OutputSanitizer intercepts and redacts the secrets before returning safe content.
4. **Idempotency Protection**: Repeated tool calls with the same idempotency key return cached results without re-executing side-effects.
5. **Red Team Security Benchmark**: Runs the automated security corpus evaluating defenses against injection, leakage, and evasion.
6. **Telemetry & Cost Tracking**: Accurately tracks token counts, estimated USD cost, and latency.
7. **Unified Report**: Produces `.sentinel/report.json` and `.sentinel/report.md`.

## How to Run:

```bash
# Using CLI subcommand
python -m sentinel.cli demo-agent

# Or running direct script
python demo/sentinel-x-agent/agent_mock.py
```

Then open the dashboard:
```bash
python -m sentinel.cli ui
```
