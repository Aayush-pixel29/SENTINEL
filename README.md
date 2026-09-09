# Sentinel

> **AI writes the code. Sentinel verifies what can actually be verified.**

## The Problem
AI coding increases development speed but shifts effort toward verification and review. An AI coding agent can tell you its implementation is correct, but *another AI opinion isn't proof*. The cost of generating code is falling faster than the cost of trusting it.

## The Solution
Sentinel provides a local verification layer that runs actual engineering checks and independently reviews AI-generated changes. 

Sentinel separates deterministic evidence from AI reasoning and clearly labels what is confirmed, unconfirmed, unavailable or incomplete.

## Why Sentinel is different
- **AI opinion ≠ proof**: We don't replace real checks with LLMs.
- **CONFIRMED vs UNCONFIRMED**: A SQL injection found by Semgrep is *Confirmed*. A potential authorization issue raised by an LLM is *Unconfirmed*.

## Architecture
```
Git Diff -> Subprocess Check Engine (pytest, ruff, mypy, semgrep, gitleaks, pip-audit)
          -> Independent AI Review (Claude)
          -> Evidence Synthesis Engine
          -> Verdict (BLOCKED / REVIEW / VERIFIED / INCOMPLETE)
```

## Installation
```bash
git clone https://github.com/example/sentinel.git
cd sentinel
pip install -e .
```

## Configuration
Create a `.sentinel/config.yml` in your project root:
```yaml
project:
  name: demo-app
  language: python

checks:
  test:
    enabled: true
    command: "pytest"
```

Set your API key for the AI Critic:
```bash
export ANTHROPIC_API_KEY="sk-..."
```

## Usage
Run verification:
```bash
sentinel verify
```

Generate an AI Use Declaration:
```bash
sentinel declare
```

## Security & Responsible AI
Sentinel does not execute AI-generated exploit payloads. It is a local tool designed to assist human judgment, not replace it. Sentinel does not claim that AI-generated software is safe because an AI said it was safe. Deterministic findings are reported separately from AI suspicions. A clean report does not guarantee completely secure software.

## Limitations
- No guarantee of absolute security
- AI findings can be wrong
- Scanners have coverage limitations
- Only configured checks run
- AI provider availability affects AI review

## Roadmap
- GitHub Action
- VS Code extension
- Support for JavaScript/TypeScript, Go, Rust, Java
- Multiple AI Providers
- CI Policy Enforcement
