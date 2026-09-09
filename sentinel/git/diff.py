import subprocess
from sentinel.models import GitChangeSummary


def is_git_repository() -> bool:
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, check=True, text=True, timeout=10
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_current_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def get_current_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def get_repo_name() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10
        )
        path = result.stdout.strip()
        if path:
            return path.replace("\\", "/").split("/")[-1]
        return "unknown"
    except Exception:
        return "unknown"


def get_git_diff() -> GitChangeSummary:
    if not is_git_repository():
        raise RuntimeError("Sentinel must be run inside a Git repository.")

    def run_cmd(args):
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode == 0:
            return result
        return result

    # Try staged changes first
    diff_cmd = ["git", "diff", "--cached"]
    diff_stat_cmd = ["git", "diff", "--cached", "--numstat"]
    diff_source = "staged"

    result = run_cmd(diff_cmd)
    diff_text = result.stdout if result.returncode == 0 else ""
    if not diff_text.strip():
        # Fall back to working tree diff
        diff_cmd = ["git", "diff"]
        diff_stat_cmd = ["git", "diff", "--numstat"]
        diff_source = "working-tree"
        result = run_cmd(diff_cmd)
        diff_text = result.stdout if result.returncode == 0 else ""

    # Get numstat to count added/removed lines and files
    stat_result = run_cmd(diff_stat_cmd)
    files_changed = 0
    lines_added = 0
    lines_removed = 0
    changed_files_list = []

    for line in stat_result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            added, removed, filename = parts
            if added != "-":
                lines_added += int(added)
            if removed != "-":
                lines_removed += int(removed)
            files_changed += 1
            changed_files_list.append(filename)

    return GitChangeSummary(
        files_changed=files_changed,
        lines_added=lines_added,
        lines_removed=lines_removed,
        changed_files_list=changed_files_list,
        diff_text=diff_text,
        diff_source=diff_source,
    )
