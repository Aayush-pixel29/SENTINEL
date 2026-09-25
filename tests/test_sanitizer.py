from sentinel.sanitizer import OutputSanitizer


def test_sanitize_connection_string():
    sanitizer = OutputSanitizer()
    raw = "Database connection failed.\npostgres://admin:SuperSecretPassword123@db-prod-1.internal:5432/main"
    res = sanitizer.sanitize(raw)
    assert res.sanitized is True
    assert res.redactions >= 1
    assert "credential" in res.categories
    assert "SuperSecretPassword123" not in res.safe_content
    assert "postgres://[database connection credentials redacted]@" in res.safe_content


def test_sanitize_api_keys_and_tokens():
    sanitizer = OutputSanitizer()
    raw = (
        "Found keys: sk-abcdef12345678901234567890 and "
        "AIzaSyD9876543210123456789012345678901 and "
        "ghp_123456789012345678901234567890123456 and "
        "AKIAIOSFODNN7EXAMPLE"
    )
    res = sanitizer.sanitize(raw)
    assert res.sanitized is True
    assert res.redactions == 4
    assert "secret" in res.categories
    assert "sk-abcdef" not in res.safe_content
    assert "AIzaSy" not in res.safe_content
    assert "ghp_" not in res.safe_content
    assert "AKIAIOSFODNN7EXAMPLE" not in res.safe_content


def test_sanitize_pii():
    sanitizer = OutputSanitizer()
    raw = "Contact admin at dev-security@company.internal or SSN 123-45-6789"
    res = sanitizer.sanitize(raw)
    assert res.sanitized is True
    assert "pii" in res.categories
    assert "dev-security@company.internal" not in res.safe_content
    assert "123-45-6789" not in res.safe_content


def test_sanitize_clean_output():
    sanitizer = OutputSanitizer()
    raw = "File 'utils.py' parsed cleanly with 4 functions."
    res = sanitizer.sanitize(raw)
    assert res.sanitized is False
    assert res.redactions == 0
    assert res.safe_content == raw
