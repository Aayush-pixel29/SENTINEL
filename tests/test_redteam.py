from sentinel.eval import RedTeamRunner, DatasetLoader


def test_redteam_dataset_loaded():
    cases = DatasetLoader.load_redteam_cases()
    assert len(cases) >= 6
    categories = {c.category for c in cases}
    assert "unsafe_tool_arguments" in categories
    assert "secret_leakage" in categories
    assert "pii_leakage" in categories


def test_redteam_suite_execution():
    runner = RedTeamRunner()
    report = runner.run_redteam_suite()

    # All security red-team attacks must be caught and mitigated
    assert report.total_cases >= 6
    assert report.passed == report.total_cases
    assert report.failed == 0
    assert report.task_success_rate == 1.0
