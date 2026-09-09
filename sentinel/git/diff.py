import subprocess
import os
from pathlib import Path
from sentinel.models import GitChangeSummary

def is_git_repository() -> bool:
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            check=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False

def get_git_diff() -> GitChangeSummary:
    if not is_git_repository():
        raise RuntimeError("Not inside a Git repository")

    # Try staged changes first
    diff_cmd = ["git", "diff", "--cached"]
    diff_stat_cmd = ["git", "diff", "--cached", "--numstat"]
    
    result = subprocess.run(diff_cmd, capture_output=True, text=True)
    if not result.stdout.strip():
        # Fall back to working tree diff
        diff_cmd = ["git", "diff"]
        diff_stat_cmd = ["git", "diff", "--numstat"]
        result = subprocess.run(diff_cmd, capture_output=True, text=True)

    diff_text = result.stdout

    # Get numstat to count added/removed lines and files
    stat_result = subprocess.run(diff_stat_cmd, capture_output=True, text=True)
    
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
        diff_text=diff_text
    )
