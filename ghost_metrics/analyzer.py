"""Analyze patterns in git repository data."""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AnalysisResult:
    """Complete analysis result for a repository."""
    repo_name: str
    total_commits: int = 0
    total_contributors: int = 0
    total_insertions: int = 0
    total_deletions: int = 0
    total_files_changed: int = 0
    first_commit_date: Optional[datetime] = None
    last_commit_date: Optional[datetime] = None
    active_days: int = 0
    commits_by_hour: dict = field(default_factory=dict)
    commits_by_day: dict = field(default_factory=dict)
    commits_by_month: dict = field(default_factory=dict)
    commits_by_weekday: dict = field(default_factory=dict)
    top_changed_files: list = field(default_factory=list)
    contributor_stats: list = field(default_factory=list)
    language_distribution: dict = field(default_factory=dict)
    avg_commit_size: float = 0.0
    avg_insertions: float = 0.0
    avg_deletions: float = 0.0
    commit_heatmap: dict = field(default_factory=dict)


# Map file extensions to language names
EXTENSION_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript (React)", ".jsx": "JavaScript (React)",
    ".java": "Java", ".kt": "Kotlin", ".swift": "Swift",
    ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
    ".php": "PHP", ".c": "C", ".cpp": "C++", ".h": "C/C++ Header",
    ".cs": "C#", ".scala": "Scala", ".r": "R",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".less": "LESS",
    ".json": "JSON", ".yaml": "YAML", ".yml": "YAML",
    ".xml": "XML", ".sql": "SQL", ".sh": "Shell",
    ".md": "Markdown", ".txt": "Text", ".toml": "TOML",
    ".lua": "Lua", ".dart": "Dart", ".vue": "Vue",
    ".svelte": "Svelte", ".zig": "Zig", ".nim": "Nim",
    ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang",
    ".hs": "Haskell", ".ml": "OCaml", ".clj": "Clojure",
    "(no extension)": "Other",
}


def analyze_repo(repo_data) -> AnalysisResult:
    """Run full analysis on collected repo data."""
    commits = repo_data.commits
    result = AnalysisResult(repo_name=repo_data.name)

    if not commits:
        result.language_distribution = _map_languages(repo_data.file_extensions)
        return result

    result.total_commits = len(commits)

    # Date range
    dates = [c.date for c in commits]
    result.first_commit_date = min(dates)
    result.last_commit_date = max(dates)
    result.active_days = len(set(d.date() for d in dates))

    # Totals
    result.total_insertions = sum(c.insertions for c in commits)
    result.total_deletions = sum(c.deletions for c in commits)
    result.total_files_changed = sum(c.files_changed for c in commits)

    # Averages
    result.avg_commit_size = result.total_files_changed / len(commits)
    result.avg_insertions = result.total_insertions / len(commits)
    result.avg_deletions = result.total_deletions / len(commits)

    # Commits by hour (0-23)
    hour_counts = Counter(c.date.hour for c in commits)
    result.commits_by_hour = {h: hour_counts.get(h, 0) for h in range(24)}

    # Commits by weekday (0=Monday, 6=Sunday)
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_counts = Counter(c.date.weekday() for c in commits)
    result.commits_by_weekday = {
        weekday_names[d]: weekday_counts.get(d, 0) for d in range(7)
    }

    # Commits by month (YYYY-MM)
    month_counts = Counter(c.date.strftime("%Y-%m") for c in commits)
    result.commits_by_month = dict(sorted(month_counts.items()))

    # Commits by day (YYYY-MM-DD) for heatmap
    day_counts = Counter(c.date.strftime("%Y-%m-%d") for c in commits)
    result.commits_by_day = dict(sorted(day_counts.items()))

    # Heatmap: weekday x hour
    heatmap = defaultdict(lambda: defaultdict(int))
    for c in commits:
        heatmap[c.date.weekday()][c.date.hour] += 1
    result.commit_heatmap = {
        weekday_names[d]: {h: heatmap[d][h] for h in range(24)}
        for d in range(7)
    }

    # Top changed files (code churn)
    file_change_counts = Counter()
    for c in commits:
        for f in c.files:
            file_change_counts[f] += 1
    result.top_changed_files = file_change_counts.most_common(20)

    # Contributor stats
    contributor_data = defaultdict(lambda: {
        "commits": 0, "insertions": 0, "deletions": 0,
        "first_commit": None, "last_commit": None, "files_touched": set()
    })
    for c in commits:
        key = f"{c.author_name} <{c.author_email}>"
        cd = contributor_data[key]
        cd["commits"] += 1
        cd["insertions"] += c.insertions
        cd["deletions"] += c.deletions
        for f in c.files:
            cd["files_touched"].add(f)
        if cd["first_commit"] is None or c.date < cd["first_commit"]:
            cd["first_commit"] = c.date
        if cd["last_commit"] is None or c.date > cd["last_commit"]:
            cd["last_commit"] = c.date

    result.contributor_stats = sorted(
        [
            {
                "name": name,
                "commits": data["commits"],
                "insertions": data["insertions"],
                "deletions": data["deletions"],
                "files_touched": len(data["files_touched"]),
                "first_commit": data["first_commit"].isoformat() if data["first_commit"] else None,
                "last_commit": data["last_commit"].isoformat() if data["last_commit"] else None,
            }
            for name, data in contributor_data.items()
        ],
        key=lambda x: x["commits"],
        reverse=True,
    )
    result.total_contributors = len(result.contributor_stats)

    # Language distribution from file extensions
    result.language_distribution = _map_languages(repo_data.file_extensions)

    return result


def _map_languages(file_extensions: dict) -> dict:
    """Map file extensions to language names and aggregate."""
    lang_counts = defaultdict(int)
    for ext, count in file_extensions.items():
        lang = EXTENSION_MAP.get(ext, ext)
        lang_counts[lang] += count
    return dict(sorted(lang_counts.items(), key=lambda x: x[1], reverse=True))
