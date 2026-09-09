const vulnerableReport = {
  "repository": "Aayush-pixel29/SENTINEL",
  "branch": "feature/user-profile",
  "commit": "a84c2d1",
  "timestamp": "2026-09-09T20:00:00Z",
  "verdict": "BLOCKED",
  "checks": [
    {"name": "pytest", "status": "PASSED"},
    {"name": "ruff", "status": "PASSED"},
    {"name": "mypy", "status": "PASSED"},
    {"name": "semgrep", "status": "FAILED"},
    {"name": "gitleaks", "status": "PASSED"},
    {"name": "pip-audit", "status": "PASSED"}
  ],
  "confirmed_findings": [
    {
      "title": "SQL Injection",
      "severity": "ERROR",
      "classification": "CONFIRMED",
      "file": "demo/vulnerable-fastapi/main.py",
      "line": 28,
      "source": "semgrep",
      "description": "Unsafe SQL construction pattern detected.",
      "evidence": "Semgrep detected string interpolation inside SQL construction.",
      "recommendation": "Use parameterized queries."
    }
  ],
  "unconfirmed_findings": [
    {
      "title": "Authorization Boundary",
      "severity": "MEDIUM",
      "classification": "UNCONFIRMED",
      "file": "demo/vulnerable-fastapi/main.py",
      "line": 28,
      "source": "Gemini Critic",
      "description": "Possible authorization boundary issue.",
      "evidence": "The endpoint retrieves a user profile by ID without verifying if the requesting user has permission to view it.",
      "recommendation": "Check if the `current_user.id` matches the requested `user_id`."
    }
  ],
  "metadata": {
    "diff_text": "diff --git a/demo/vulnerable-fastapi/main.py b/demo/vulnerable-fastapi/main.py\n@@ -27,2 +27,2 @@\n-    # Safe query\n-    query = \"SELECT * FROM users WHERE id = ?\"\n+    # Unsafe query\n+    query = f\"SELECT * FROM users WHERE id = {user_id}\""
  }
};

const fixedReport = {
  "repository": "Aayush-pixel29/SENTINEL",
  "branch": "feature/user-profile",
  "commit": "b95d3e2",
  "timestamp": "2026-09-09T20:10:00Z",
  "verdict": "VERIFIED",
  "checks": [
    {"name": "pytest", "status": "PASSED"},
    {"name": "ruff", "status": "PASSED"},
    {"name": "mypy", "status": "PASSED"},
    {"name": "semgrep", "status": "PASSED"},
    {"name": "gitleaks", "status": "PASSED"},
    {"name": "pip-audit", "status": "PASSED"}
  ],
  "confirmed_findings": [],
  "unconfirmed_findings": [],
  "metadata": {
    "diff_text": "diff --git a/demo/vulnerable-fastapi/main.py b/demo/vulnerable-fastapi/main.py\n@@ -27,2 +27,4 @@\n-    # Unsafe query\n-    query = f\"SELECT * FROM users WHERE id = {user_id}\"\n+    if current_user.id != user_id:\n+        raise HTTPException(status_code=403, detail=\"Forbidden\")\n+    # Safe query\n+    query = \"SELECT * FROM users WHERE id = %s\""
  }
};
