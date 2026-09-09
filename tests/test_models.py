from sentinel.models import Finding, Classification

def test_finding_creation():
    f = Finding(
        id="test-1",
        source="pytest",
        classification=Classification.CONFIRMED,
        severity="HIGH",
        title="Test Failed",
        description="A test failed"
    )
    assert f.title == "Test Failed"
    assert f.classification == Classification.CONFIRMED
