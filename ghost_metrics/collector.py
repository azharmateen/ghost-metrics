"""Collect git data locally by parsing git log. No API calls needed."""

import os
import subprocess
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Commit:
    hash: str
    author_name: str
    author_email: str
    date: datetime
    message: str
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    files: list = field(default_factory=list)


@dataclass
class RepoData:
    path: str
    name: str
    commits: list = field(default_factory=list)
    branches: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    total_files: int = 0
    file_extensions: dict = field(default_factory=dict)


def _run_git(repo_path: str, args: list) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git", "-C", repo_path] + args,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.stdout.strip()


def _parse_numstat_line(line: str) -> tuple:
    """Parse a numstat line like '10\t5\tfile.py' into (insertions, deletions, filename)."""
    parts = line.split("\t")
    if len(parts) >= 3:
        ins = int(parts[0]) if parts[0] != "-" else 0
        dels = int(parts[1]) if parts[1] != "-" else 0
        return ins, dels, parts[2]
    return 0, 0, ""


def collect_commits(repo_path: str, max_commits: int = 10000) -> list:
    """Parse git log for commits with full metadata."""
    separator = "---GHOST_SEP---"
    fmt = f"%H{separator}%an{separator}%ae{separator}%aI{separator}%s"

    raw = _run_git(repo_path, [
        "log", f"--format={fmt}", "--numstat", f"-n{max_commits}"
    ])

    if not raw:
        return []

    commits = []
    current_commit = None
    current_files = []
    current_insertions = 0
    current_deletions = 0

    for line in raw.split("\n"):
        if separator in line:
            # Save previous commit
            if current_commit is not None:
                current_commit.files = current_files
                current_commit.files_changed = len(current_files)
                current_commit.insertions = current_insertions
                current_commit.deletions = current_deletions
                commits.append(current_commit)

            parts = line.split(separator)
            if len(parts) >= 5:
                try:
                    date = datetime.fromisoformat(parts[3])
                except (ValueError, IndexError):
                    date = datetime.now()

                current_commit = Commit(
                    hash=parts[0],
                    author_name=parts[1],
                    author_email=parts[2],
                    date=date,
                    message=parts[4],
                )
                current_files = []
                current_insertions = 0
                current_deletions = 0
        elif line.strip() and current_commit is not None:
            ins, dels, fname = _parse_numstat_line(line)
            if fname:
                current_files.append(fname)
                current_insertions += ins
                current_deletions += dels

    # Don't forget the last commit
    if current_commit is not None:
        current_commit.files = current_files
        current_commit.files_changed = len(current_files)
        current_commit.insertions = current_insertions
        current_commit.deletions = current_deletions
        commits.append(current_commit)

    return commits


def collect_branches(repo_path: str) -> list:
    """Get all branches."""
    raw = _run_git(repo_path, ["branch", "-a", "--format=%(refname:short)"])
    return [b.strip() for b in raw.split("\n") if b.strip()]


def collect_tags(repo_path: str) -> list:
    """Get all tags."""
    raw = _run_git(repo_path, ["tag", "--list"])
    return [t.strip() for t in raw.split("\n") if t.strip()]


def collect_file_extensions(repo_path: str) -> dict:
    """Count files by extension in the current tree."""
    raw = _run_git(repo_path, ["ls-files"])
    ext_counts = {}
    total = 0
    for fpath in raw.split("\n"):
        fpath = fpath.strip()
        if not fpath:
            continue
        total += 1
        _, ext = os.path.splitext(fpath)
        ext = ext.lower() if ext else "(no extension)"
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
    return ext_counts, total


def collect_repo(repo_path: str, max_commits: int = 10000) -> RepoData:
    """Collect all data for a repository."""
    repo_path = os.path.abspath(repo_path)

    # Get repo name from remote or directory
    remote = _run_git(repo_path, ["remote", "get-url", "origin"])
    if remote:
        name = remote.rstrip("/").split("/")[-1].replace(".git", "")
    else:
        name = os.path.basename(repo_path)

    commits = collect_commits(repo_path, max_commits)
    branches = collect_branches(repo_path)
    tags = collect_tags(repo_path)
    file_extensions, total_files = collect_file_extensions(repo_path)

    return RepoData(
        path=repo_path,
        name=name,
        commits=commits,
        branches=branches,
        tags=tags,
        total_files=total_files,
        file_extensions=file_extensions,
    )
