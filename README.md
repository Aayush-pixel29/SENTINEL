# SENTINEL-X

### AI Agent Reliability, Security & Verification Control Plane

[![CI/CD Verification Gate](https://github.com/Aayush-pixel29/SENTINEL/actions/workflows/sentinel.yml/badge.svg)](https://github.com/Aayush-pixel29/SENTINEL/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> **AI writes the code & proposes actions. SENTINEL-X verifies what can be deterministically proven. Humans make the final decision.**

---

## 1. The Problem

The marginal cost of generating code and autonomous AI agent workflows is plummeting toward zero. However, the cost of **trusting and securing** autonomous agents is skyrocketing:

- **Unrestricted Tool Abuse**: Persuasive adversarial prompts can coerce agents into invoking dangerous tools (e.g. raw shell commands, internal network fetches).
- **Silent Credential Leakage**: Agents fetching configs or database strings unintentionally leak passwords, tokens, and PII into context windows and log streams.
- **Flaky Execution & Side-Effect Duplication**: Lack of idempotency and checkpoint recovery causes unpredictable agent loops and duplicate side-effects.
- **Unverified Hallucinations**: An LLM claiming *"Tests pass and code is safe"* provides zero mathematical or deterministic assurance.

**The cost of generating AI code is falling faster than the cost of verifying it.**

---

## 2. The SENTINEL-X Solution

**SENTINEL-X** is an open-source, local-first control plane that wraps AI agents and development workflows in a hardened verification boundary:

```text
┌────────────────────────────────────────────────────────┐
│                   AI / AGENT WORKFLOW                  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                SENTINEL-X CONTROL PLANE                │
│                                                        │
│  ├── 🛡 ToolShield Policy Engine (Allow/Deny/Review)   │
│  ├── 🔒 Output Sanitizer (Secrets / Credentials / PII) │
│  ├── ⚡ Execution Manager (Idempotency & Retries)      │
│  ├── 💾 Checkpoint & Recovery (Step Resumption)        │
│  ├── 📊 Deterministic Evaluation & Red Team Suite      │
│  ├── ⏱ Unified Event Traces (Waterfall Spans)          │
│  ├── 💰 Cost & Latency Telemetry (Normalized Pricing)  │
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
│        (VS Code Extension, Web Dashboard, CI/CD)       │
└────────────────────────────────────────────────────────┘
```

---

## 3. Core Capabilities

### 🛡 ToolShield Security Policy Engine (`sentinel/shield/`)
- **Explicit Tool Registry**: Hardened contracts with metadata: `trust_level` (`verified`, `trusted`, `unknown`, `blocked`), `risk` (`low`, `medium`, `high`, `critical`), and allowed operations.
- **Deterministic Policy Pipeline**: Evaluates tool requests (`ALLOW`, `DENY`, `REVIEW`) without trusting LLM self-assessments.
- **Injection Defense**: Scans arguments for path traversal (`../`), command chaining (`;`, `|`, `&&`), and shell pipes.

### 🔒 Zero-Loss Tool Output Sanitizer (`sentinel/sanitizer/`)
- Intercepts raw tool outputs before they enter agent context.
- Detects and redacts database connection strings, API keys (OpenAI, Gemini, GitHub, AWS), Bearer tokens, private keys, and PII.

### ⚡ Execution Reliability & Checkpoints (`sentinel/reliability/`)
- **Idempotency & Duplicate Protection**: Prevents duplicate executions of side-effects using idempotency keys and state caching.
- **Resilient Retries**: Configurable exponential backoff for transient network glitches.
- **Step Checkpoints**: Lightweight snapshotting enabling execution resumption without re-running completed steps.

### 📊 Deterministic Evaluation & Red Team Suite (`sentinel/eval/`)
- **Deterministic Scorecards**: Benchmarks task success, tool selection, argument safety, output validity, latency, and cost.
- **Red Team Corpus**: Built-in adversarial dataset covering prompt injection, evasion, secret extraction, and path traversal.

### 💰 Cost & Latency Telemetry (`sentinel/metrics/`)
- Normalized token accounting and pricing adapters for Google Gemini, OpenAI, Claude, and local models.

---

## 4. Installation & Quickstart

### Prerequisites
- Python 3.9+
- Git

### 1. Install SENTINEL-X Engine
```bash
git clone https://github.com/Aayush-pixel29/SENTINEL.git
cd SENTINEL
pip install -e .
```

### 2. Optional: Configure AI Critic (Gemini)
```bash
export GEMINI_API_KEY="your_api_key_here"      # Linux / macOS
$env:GEMINI_API_KEY="your_api_key_here"        # PowerShell
```
*(Note: SENTINEL-X deterministic checks, ToolShield, Sanitizer, and Evaluations run 100% locally even without an API key).*

---

## 5. CLI Command Reference

| Command | Description |
|:---|:---|
| `sentinel verify` | Run full verification pipeline on local Git changes |
| `sentinel verify --eval` | Run verification + deterministic evaluation benchmark |
| `sentinel redteam` | Run adversarial Red Team security test suite |
| `sentinel eval` | Run deterministic evaluation test cases |
| `sentinel trace [run_id]` | Inspect event spans, latency waterfall, and token costs |
| `sentinel demo-agent` | Run interactive mock agent demo illustrating safety barriers |
| `sentinel ui` | Launch local interactive web control plane dashboard |
| `sentinel explain` | Explain verification verdict and evidence in plain English |
| `sentinel declare` | Generate compliant `AI_USE_DECLARATION.md` |

---

## 6. End-to-End Demo Scenario

Run the autonomous mock agent demo to see the safety barriers in action:

```bash
# Run the local mock agent demo
sentinel demo-agent
```

**What the demo validates:**
1. **Adversarial Tool Blockade**: Agent requests `raw_bash_exec` (`cat /etc/shadow`) -> **DENIED** by ToolShield.
2. **Path Traversal Interception**: Agent requests `../../../../etc/passwd` -> **DENIED** by ArgumentValidator.
3. **Output Sanitization**: Authorized database read containing plaintext connection passwords & emails -> Redacted automatically.
4. **Idempotency Protection**: Duplicate execution request returns cached result with zero duplicate side-effects.
5. **Red Team Suite**: All 6 adversarial attacks evaluated and mitigated (100.0% pass rate).
6. **Telemetry & Report**: Full run trace and cost logged to `.sentinel/report.json`.

Open the visual dashboard:
```bash
sentinel ui
```

---

## 7. VS Code Extension

SENTINEL-X integrates directly into VS Code:

1. Open the repository root in VS Code.
2. Open the `vscode-extension` directory and press `F5` to start the Extension Host.
3. Click the 🛡 **Sentinel-X** icon in the Activity Bar.
4. Click **Verify Changes** to run the control plane and view findings directly mapped to file lines.

---

## 8. Philosophy: CONFIRMED vs UNCONFIRMED

SENTINEL-X strictly separates deterministic proof from probabilistic AI suggestions:

| Finding Type | Source | Definition |
|:---|:---|:---|
| **CONFIRMED** | Deterministic tools (Semgrep, Pytest, Gitleaks, Pip-audit) | **Mathematical / AST fact**. Triggers `BLOCKED` verdict if high severity. |
| **UNCONFIRMED** | AI Critic / Agent Hypotheses | **Probabilistic concern**. Triggers `REVIEW` verdict; requires human decision. |

### Verdict Hierarchy
```text
BLOCKED  ──▶ Critical confirmed vulnerabilities or failing unit tests
   │
INCOMPLETE ──▶ Missing verification tools or unhandled exceptions
   │
REVIEW   ──▶ Unconfirmed AI concerns or non-blocking findings
   │
VERIFIED ──▶ All required checks passed cleanly
```

---

## 9. Security & Threat Model

See [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) for full threat analysis and trust boundary specifications.

**Key Invariants:**
- No arbitrary remote script execution without explicit allowlist policy.
- No raw tool trust based on LLM opinion.
- All secrets, API keys, and connection credentials redacted before entering logs or context.

---

## 10. Documentation Index

- [Architecture Specification](docs/ARCHITECTURE.md)
- [Threat Model & Security Spec](docs/THREAT_MODEL.md)
- [Evaluation & Benchmark Framework](docs/EVALUATION.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Changelog](CHANGELOG.md)

---

## 11. Roadmap

- [x] Unified Run & Event Trace Model (Spans, JSONL)
- [x] ToolShield Security & Policy Engine (Allow/Deny/Review)
- [x] Output Sanitizer (Credentials, Tokens, PII)
- [x] Execution Reliability & Idempotency Layer
- [x] Checkpoint & Step Recovery Model
- [x] Deterministic Evaluation Runner & Red Team Suite
- [x] Normalized Cost & Latency Telemetry
- [x] Model Routing Abstraction
- [x] GitHub Actions CI/CD Security Gate
- [x] VS Code Extension & Web Dashboard Upgrade
- [ ] Multi-tenant Sandboxed Container Gateway (gVisor/Wasm)
- [ ] Enterprise Webhook Alerting (Slack/Teams/PagerDuty)

---

## 12. License

MIT License. See [LICENSE](LICENSE) for details.
