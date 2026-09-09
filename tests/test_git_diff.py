from sentinel.models import GitChangeSummary


def test_git_change_summary_model():
    summary = GitChangeSummary(
        files_changed=2,
        lines_added=10,
        lines_removed=5,
        changed_files_list=["main.py", "test.py"],
        diff_text="fake diff",
        diff_source="staged",
    )
    assert summary.files_changed == 2
    assert "main.py" in summary.changed_files_list
    assert summary.diff_source == "staged"


def test_git_change_summary_default_source():
    summary = GitChangeSummary(
        files_changed=0,
        lines_added=0,
        lines_removed=0,
        changed_files_list=[],
        diff_text="",
    )
    assert summary.diff_source == "working-tree"
