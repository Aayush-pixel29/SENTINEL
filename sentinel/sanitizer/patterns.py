import re
from typing import List, Tuple

# Tuples of (Category, Pattern, Replacement)
SANITIZATION_RULES: List[Tuple[str, re.Pattern, str]] = [
    # 1. Connection strings with credentials
    (
        "credential",
        re.compile(r"(?i)\b(postgres|postgresql|mysql|mongodb|redis|amqp|mssql):\/\/[^\s:]+:([^\s@]+)@", re.IGNORECASE),
        r"\1://[database connection credentials redacted]@",
    ),
    # 2. OpenAI / Anthropic / Gemini / Generic API keys
    (
        "secret",
        re.compile(r"\b(sk-[a-zA-Z0-9_-]{20,})\b"),
        "[REDACTED_API_KEY]",
    ),
    (
        "secret",
        re.compile(r"\b(AIzaSy[a-zA-Z0-9_-]{30,40})\b"),
        "[REDACTED_GEMINI_API_KEY]",
    ),
    (
        "secret",
        re.compile(r"\b(ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59})\b"),
        "[REDACTED_GITHUB_TOKEN]",
    ),
    (
        "secret",
        re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        "[REDACTED_AWS_ACCESS_KEY]",
    ),
    (
        "secret",
        re.compile(r"(?i)bearer\s+([a-zA-Z0-9\-_\.]{20,})"),
        "Bearer [REDACTED_BEARER_TOKEN]",
    ),
    # 3. Private keys
    (
        "secret",
        re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH|PRIVATE) KEY-----[\s\S]*?-----END \1 KEY-----"),
        "[REDACTED_PRIVATE_KEY_BLOCK]",
    ),
    # 4. Cloud instance metadata service (IMDS) endpoints
    (
        "security_risk",
        re.compile(r"http://169\.254\.169\.254[^\s]*"),
        "[REDACTED_CLOUD_METADATA_URL]",
    ),
    # 5. PII (Emails & SSNs)
    (
        "pii",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
    (
        "pii",
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "[REDACTED_SSN]",
    ),
]
