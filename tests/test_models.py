from sentinel.models import Finding, Classification, CheckStatus, AIReviewResult


def test_finding_creation():
    f = Finding(
        id="test-1",
        source="pytest",
        classification=Classification.CONFIRMED,
        severity="HIGH",
        title="Test Failed",
        description="A test failed",
    )
    assert f.title == "Test Failed"
    assert f.classification == Classification.CONFIRMED


def test_ai_review_result_default_provider():
    r = AIReviewResult(summary="ok", findings=[])
    assert r.provider == "gemini"
    assert r.status == CheckStatus.PASSED
