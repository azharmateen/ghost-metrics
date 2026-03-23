"""Export repository analytics in multiple formats."""

import json
import csv
import io
import os
from datetime import datetime


def export_json(analysis, trends) -> str:
    """Export analysis and trends as JSON."""
    data = {
        "repo_name": analysis.repo_name,
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_commits": analysis.total_commits,
            "total_contributors": analysis.total_contributors,
            "total_insertions": analysis.total_insertions,
            "total_deletions": analysis.total_deletions,
            "active_days": analysis.active_days,
            "avg_commit_size": round(analysis.avg_commit_size, 2),
            "avg_insertions": round(analysis.avg_insertions, 2),
            "avg_deletions": round(analysis.avg_deletions, 2),
        },
        "date_range": {
            "first_commit": analysis.first_commit_date.isoformat() if analysis.first_commit_date else None,
            "last_commit": analysis.last_commit_date.isoformat() if analysis.last_commit_date else None,
        },
        "trends": {
            "activity_trend": trends.activity_trend,
            "activity_details": trends.activity_details,
            "bus_factor": trends.bus_factor,
            "bus_factor_contributors": trends.bus_factor_contributors,
            "is_weekend_warrior": trends.is_weekend_warrior,
            "weekend_commit_pct": round(trends.weekend_commit_pct, 1),
            "is_night_owl": trends.is_night_owl,
            "night_commit_pct": round(trends.night_commit_pct, 1),
            "is_early_bird": trends.is_early_bird,
            "morning_commit_pct": round(trends.morning_commit_pct, 1),
            "most_active_day": trends.most_active_day,
            "most_active_hour": trends.most_active_hour,
            "avg_commits_per_week": round(trends.avg_commits_per_week, 1),
            "longest_gap_days": trends.longest_gap_days,
            "days_since_last_commit": trends.days_since_last_commit,
            "stale": trends.stale,
            "seasonal_pattern": trends.seasonal_pattern,
        },
        "commits_by_hour": analysis.commits_by_hour,
        "commits_by_weekday": analysis.commits_by_weekday,
        "commits_by_month": analysis.commits_by_month,
        "top_changed_files": [{"file": f, "changes": c} for f, c in analysis.top_changed_files],
        "contributors": analysis.contributor_stats,
        "language_distribution": analysis.language_distribution,
    }
    return json.dumps(data, indent=2, default=str)


def export_csv(analysis) -> str:
    """Export contributor and commit data as CSV."""
    output = io.StringIO()

    # Contributors CSV
    writer = csv.writer(output)
    writer.writerow(["# Contributors"])
    writer.writerow(["Name", "Commits", "Insertions", "Deletions", "Files Touched", "First Commit", "Last Commit"])
    for c in analysis.contributor_stats:
        writer.writerow([
            c["name"], c["commits"], c["insertions"], c["deletions"],
            c["files_touched"], c["first_commit"], c["last_commit"]
        ])

    writer.writerow([])
    writer.writerow(["# Monthly Activity"])
    writer.writerow(["Month", "Commits"])
    for month, count in sorted(analysis.commits_by_month.items()):
        writer.writerow([month, count])

    writer.writerow([])
    writer.writerow(["# Top Changed Files"])
    writer.writerow(["File", "Times Changed"])
    for f, c in analysis.top_changed_files:
        writer.writerow([f, c])

    writer.writerow([])
    writer.writerow(["# Language Distribution"])
    writer.writerow(["Language", "File Count"])
    for lang, count in analysis.language_distribution.items():
        writer.writerow([lang, count])

    return output.getvalue()


def export_markdown(analysis, trends) -> str:
    """Export analysis as Markdown summary."""
    lines = []
    lines.append(f"# {analysis.repo_name} - Analytics Report")
    lines.append(f"\n*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by Ghost Metrics*\n")

    lines.append("## Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Commits | {analysis.total_commits:,} |")
    lines.append(f"| Contributors | {analysis.total_contributors} |")
    lines.append(f"| Lines Added | +{analysis.total_insertions:,} |")
    lines.append(f"| Lines Deleted | -{analysis.total_deletions:,} |")
    lines.append(f"| Active Days | {analysis.active_days} |")
    lines.append(f"| Avg Commit Size | {analysis.avg_insertions + analysis.avg_deletions:.0f} lines |")
    if analysis.first_commit_date:
        lines.append(f"| First Commit | {analysis.first_commit_date.strftime('%Y-%m-%d')} |")
    if analysis.last_commit_date:
        lines.append(f"| Last Commit | {analysis.last_commit_date.strftime('%Y-%m-%d')} |")

    lines.append("\n## Trends\n")
    lines.append(f"- **Activity**: {trends.activity_trend} - {trends.activity_details}")
    lines.append(f"- **Bus Factor**: {trends.bus_factor}")
    lines.append(f"- **Velocity**: {trends.avg_commits_per_week:.1f} commits/week")
    if trends.is_weekend_warrior:
        lines.append(f"- **Weekend Warrior**: {trends.weekend_commit_pct:.1f}% weekend commits")
    if trends.is_night_owl:
        lines.append(f"- **Night Owl**: {trends.night_commit_pct:.1f}% commits 10pm-4am")
    lines.append(f"- **Most Active**: {trends.most_active_day} at {trends.most_active_hour}:00")
    if trends.stale:
        lines.append(f"- **STALE**: {trends.days_since_last_commit} days since last commit")

    lines.append("\n## Top Contributors\n")
    lines.append("| Name | Commits | Lines Added | Lines Deleted |")
    lines.append("|------|---------|-------------|---------------|")
    for c in analysis.contributor_stats[:10]:
        name = c["name"].split(" <")[0]
        lines.append(f"| {name} | {c['commits']} | +{c['insertions']:,} | -{c['deletions']:,} |")

    lines.append("\n## Most Changed Files\n")
    lines.append("| File | Changes |")
    lines.append("|------|---------|")
    for f, count in analysis.top_changed_files[:10]:
        lines.append(f"| `{f}` | {count} |")

    lines.append("\n## Languages\n")
    lines.append("| Language | Files |")
    lines.append("|----------|-------|")
    for lang, count in list(analysis.language_distribution.items())[:10]:
        lines.append(f"| {lang} | {count} |")

    lines.append("\n---\n*Report by [Ghost Metrics](https://github.com/ghost-metrics/ghost-metrics) - 100% offline analytics*")

    return "\n".join(lines)


def save_export(content: str, filepath: str) -> str:
    """Save exported content to file."""
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(filepath)
