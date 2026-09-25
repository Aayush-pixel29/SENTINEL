# SENTINEL-X

### AI Agent Reliability, Security & Verification Control Plane

[![CI/CD Verification Gate](https://github.com/Aayush-pixel29/SENTINEL/actions/workflows/sentinel.yml/badge.svg)](https://github.com/Aayush-pixel29/SENTINEL/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests: 44 Passing](https://img.shields.io/badge/tests-44%20passed-success.svg)](tests/)

> **Problem**: The marginal cost of generating AI code and agent workflows is plummeting toward zero, but the cost of verifying, securing, and trusting autonomous tool execution is skyrocketing.
>
> **Solution**: SENTINEL-X is an open-source, local-first control plane that enforces deterministic tool security policies, redacts leaked credentials, prevents duplicate side-effects, scores agent safety benchmarks, and verifies code before humans decide to merge.

---

## 1. Core Architecture

```text
┌────────────────────────────────────────────────────────┐
│                   AI / AGENT WORKFLOW                  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                SENTINEL-X CONTROL PLANE                │
│                                                        │
│  ├── 🛡 ToolShield Policy Engine (Allow / Deny / Review)│
│  ├── 🔒 Output Sanitizer (Secrets / Credentials / PII) │
│  ├── 🔌 MCP-Compatible Tool Security Gateway          │
│  ├── ⚡ Execution Manager (Idempotency & Retries)      │
│  ├── 💾 Checkpoint & Recovery (Step Resumption)        │
│  ├── 📊 Deterministic Evaluation & Red Team Suite      │
│  ├── ⏱ Unified Event Traces (Waterfall Spans, JSONL)   │
│  ├── 💰 Cost & Latency Telemetry (Normalized Pricing)  │
│  ├── 🔀 Rule-Based Model Routing Abstraction           │
│  └── 🔍 Code Verification (Pytest, Semgrep, Gitleaks)  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             EVIDENCE & TELEMETRY REPORT                │
│       (.sentinel/report.json & .sentinel/report.md)    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│           HUMAN DECISION & CI/CD QUALITY GATE          │
│   (VS Code Extension, Web Dashboard, GitHub Actions)   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Feature Matrix

| Subsystem | Capability | Current Implementation Scope |
|:---|:---|:---|
| **ToolShield** | Deterministic Tool Policy Engine | Explicit registry (`verified`, `trusted`, `unknown`, `blocked`), policy checks (`ALLOW`/`DENY`/`REVIEW`), argument injection & path-traversal validator. |
| **Output Sanitizer** | Zero-Loss Secret Interceptor | Regex-based redaction of connection strings, API keys (OpenAI, Gemini, AWS, GitHub), Bearer tokens, private keys, and PII. |
| **MCP Gateway** | MCP-Compatible Tool Gateway | Registers MCP-shaped schemas, binds local handlers, enforces ToolShield permissions, sanitizes outputs, and logs audit traces. |
| **Execution Reliability** | Fault Tolerance & Idempotency | `ExecutionManager` tracking execution states, retry backoff, and duplicate protection via idempotency keys. |
| **Checkpoint / Recovery** | Resilient State Snapshots | Saves and loads step states; enables resuming failed runs without re-running completed side-effects. |
| **Evaluation Engine** | Deterministic Benchmarking | Automated test runner scoring task success, tool selection, safety, groundedness, latency, and cost. |
| **Red Team Corpus** | Adversarial Security Suite | Evaluates defenses against prompt injection, tool hijacking, path traversal, and secret exfiltration (**6/6 test cases mitigated**). |
| **Cost & Latency** | Telemetry Accounting | Normalized token usage and pricing adapter (Gemini, OpenAI, Claude, Local) computing estimated USD expenditure. |
| **Model Router** | Model Routing Abstraction | Rule-based model selection directing tasks to `cheap`, `standard`, or `reasoning` tiers with fallback chains. |
| **Code Verification** | Multi-engine code analysis | Deterministic tools (Pytest, Semgrep, Gitleaks, Pip-audit, Ruff, Mypy) paired with an independent Gemini AI critic. |

---

## 3. Quickstart (2-Minute Demo)

### 1. Installation
```bash
git clone https://github.com/Aayush-pixel29/SENTINEL.git
cd SENTINEL
pip install -e .
```

### 2. Run the Autonomous Mock Agent Demo
```bash
sentinel demo-agent
```
**Demonstrates in real-time:**
1. **Adversarial Tool Blockade**: Agent requests `raw_bash_exec` $\rightarrow$ **DENIED** by ToolShield.
2. **Path Traversal Defense**: Agent requests `../../../../etc/passwd` $\rightarrow$ **DENIED** by ArgumentValidator.
3. **Output Sanitization**: Database query returning raw connection passwords $\rightarrow$ Redacted automatically.
4. **Idempotency Protection**: Duplicate request returns cached result with zero duplicate side-effects.
5. **Red Team Suite**: 6/6 attacks in the deterministic corpus mitigated.
6. **Telemetry & Report**: Full run trace and cost logged to `.sentinel/report.json`.

### 3. Open the Interactive Web Control Plane
```bash
sentinel ui
```
Navigate to `http://127.0.0.1:5000` to inspect the visual event waterfall, ToolShield decisions, and evaluation scorecards.

---

## 4. CLI Command Reference

```bash
sentinel verify          # Run verification on Git changes
sentinel verify --eval   # Run verification + evaluation benchmark
sentinel demo-agent      # Run end-to-end autonomous agent safety demo
sentinel redteam         # Run adversarial Red Team security corpus
sentinel eval            # Run deterministic evaluation benchmark
sentinel trace           # Inspect event spans, latency, and costs
sentinel ui              # Launch local interactive web control plane
sentinel explain         # Explain verification verdict in plain English
sentinel declare         # Generate compliant AI_USE_DECLARATION.md
```

---

## 5. VS Code Extension

SENTINEL-X integrates directly into VS Code:
1. Open the repository root in VS Code.
2. Open [`vscode-extension/`](vscode-extension/) and press `F5` to launch the Extension Host.
3. Click the 🛡 **Sentinel-X** icon in the Activity Bar.
4. Click **Verify Changes** to run the control plane and navigate directly to findings in your source code.

---

## 6. Security Philosophy & Threat Model

SENTINEL-X strictly separates deterministic facts from probabilistic AI reasoning:

| Finding Type | Source | Definition |
|:---|:---|:---|
| **CONFIRMED** | Deterministic tools (Semgrep, Pytest, Gitleaks) | **Mathematical / AST fact**. Triggers `BLOCKED` verdict on high/critical findings. |
| **UNCONFIRMED** | AI Critic (Gemini) / Agent Hypotheses | **Probabilistic concern**. Triggers `REVIEW` verdict; requires human decision. |

### Red Team Benchmark Results
In our deterministic adversarial corpus ([`sentinel/eval/datasets/redteam_cases.json`](sentinel/eval/datasets/redteam_cases.json)), **6/6 attacks were mitigated**:
- Path traversal in tool arguments (`rt_001`): **Blocked**
- Command injection payloads (`rt_002`): **Blocked**
- Persuasive unallowlisted tool request (`rt_003`): **Blocked**
- Output secret & credential leakage (`rt_004`): **Redacted**
- Shell pipe hijacking (`rt_005`): **Blocked**
- PII exfiltration (`rt_006`): **Redacted**

*(See [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) for full threat analysis).*

---

## 7. Known Scope & Limitations

1. **Rule-Based Model Router**: `ModelRouter` is currently an architectural abstraction that selects model tiers and fallback chains based on static budget and latency rules. It does not perform dynamic runtime model switching or self-optimizing cost routing.
2. **MCP Gateway Scope**: `MCPGateway` is an MCP-compatible tool adapter for registering schemas and executing local Python handlers under ToolShield governance. It does not yet implement a full remote JSON-RPC transport client.
3. **Regex-Based Sanitization**: The output sanitizer employs pattern matching for known token formats, connection URIs, private keys, and standard PII. Custom unstructured secrets should additionally be protected via environment segregation.
4. **Local Execution Scope**: The execution reliability manager provides in-process duplicate protection and local checkpointing. It is designed for single-node / local workflows, not distributed multi-node consensus.

---

## 8. Validation Status

**Validated locally on September 25, 2026:**
- **Platform**: Windows 11 / Python 3.13 / PowerShell
- **Test Suite**: 44 passed in 0.32s (`pytest`)
- **CLI Commands**: `verify`, `eval`, `redteam`, `trace`, `demo-agent`, `ui`, `explain`, `declare` verified working.
- **Git Working Tree**: Clean.

---

## 9. Documentation Index

- [Architecture Specification](docs/ARCHITECTURE.md)
- [Threat Model & Security Spec](docs/THREAT_MODEL.md)
- [Evaluation & Benchmark Framework](docs/EVALUATION.md)
- [2-Minute Showcase Demo](docs/DEMO.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Changelog](CHANGELOG.md)

---

## 10. Roadmap

- [x] Unified Event & Trace Spans (JSONL)
- [x] ToolShield Policy Engine & Argument Validator
- [x] Zero-Loss Output Sanitizer
- [x] MCP-Compatible Tool Security Gateway
- [x] Execution Manager & Idempotency Layer
- [x] Step Checkpoint & Recovery System
- [x] Deterministic Evaluation Runner & Red Team Corpus
- [x] Cost & Latency Telemetry Accounting
- [x] Rule-Based Model Routing Abstraction
- [x] GitHub Actions CI/CD Quality Gate
- [x] VS Code Extension & Control Plane Web Dashboard
- [ ] Remote MCP JSON-RPC Server / Client Transports
- [ ] Sandboxed MicroVM / Container Isolation Layer (gVisor/Wasm)

---

## 11. License

MIT License. See [LICENSE](LICENSE) for details.
