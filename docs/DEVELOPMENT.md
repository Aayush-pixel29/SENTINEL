# SENTINEL-X Development & Contributing Guide

## 1. Local Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Aayush-pixel29/SENTINEL.git
   cd SENTINEL
   ```

2. **Install in editable mode with development dependencies:**
   ```bash
   python -m pip install -e .
   python -m pip install pytest ruff mypy
   ```

3. **Verify installation:**
   ```bash
   python -m pytest
   sentinel --help
   ```

---

## 2. Project Architecture Layout

- `sentinel/events/`: Unified event and trace span model, JSONL storage.
- `sentinel/shield/`: ToolShield policy engine, tool registry, and argument validator.
- `sentinel/sanitizer/`: Credential, secret, and PII output sanitizer.
- `sentinel/reliability/`: Execution manager, retry logic, idempotency, and checkpoints.
- `sentinel/eval/`: Deterministic evaluation runner, datasets, and Red Team suite.
- `sentinel/metrics/`: Token cost calculation, pricing adapters, and latency metrics.
- `sentinel/ai/`: Model router and Gemini AI critic.
- `sentinel/checks/`: Deterministic verification runners (pytest, semgrep, gitleaks, ruff, mypy, pip-audit).
- `vscode-extension/`: VS Code extension client.
- `web-demo/`: Standalone interactive web dashboard.
- `demo/sentinel-x-agent/`: End-to-end autonomous agent safety demo.

---

## 3. Running Tests

```bash
# Run all unit and integration tests
python -m pytest

# Run Red Team tests
python -m sentinel.cli redteam

# Run evaluation suite
python -m sentinel.cli eval
```
