"""Trend detection: activity patterns, bus factor, seasonal analysis."""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TrendReport:
    """Trend analysis for a repository."""
    activity_trend: str = "stable"  # increasing, decreasing, stable
    activity_details: str = ""
    is_weekend_warrior: bool = False
    weekend_commit_pct: float = 0.0
    is_night_owl: bool = False
    night_commit_pct: float = 0.0
    is_early_bird: bool = False
    morning_commit_pct: float = 0.0
    bus_factor: int = 0
    bus_factor_contributors: list = field(default_factory=list)
    most_active_day: str = ""
    most_active_hour: int = 0
    avg_commits_per_week: float = 0.0
    commit_velocity: str = ""  # commits per active day
    longest_gap_days: int = 0
    seasonal_pattern: str = ""
    stale: bool = False
    days_since_last_commit: int = 0


def detect_trends(analysis) -> TrendReport:
    """Analyze commit patterns and detect trends."""
    report = TrendReport()

    if analysis.total_commits == 0:
        report.activity_trend = "no activity"
        report.stale = True
        return report

    commits_by_month = analysis.commits_by_month
    commits_by_weekday = analysis.commits_by_weekday
    commits_by_hour = analysis.commits_by_hour

    # Activity trend: compare first half vs second half of monthly data
    if len(commits_by_month) >= 4:
        months = sorted(commits_by_month.keys())
        mid = len(months) // 2
        first_half = sum(commits_by_month[m] for m in months[:mid])
        second_half = sum(commits_by_month[m] for m in months[mid:])
        first_avg = first_half / mid
        second_avg = second_half / (len(months) - mid)

        if second_avg > first_avg * 1.3:
            report.activity_trend = "increasing"
            pct = ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
            report.activity_details = f"Activity up ~{pct:.0f}% in recent months"
        elif second_avg < first_avg * 0.7:
            report.activity_trend = "decreasing"
            pct = ((first_avg - second_avg) / first_avg * 100) if first_avg > 0 else 0
            report.activity_details = f"Activity down ~{pct:.0f}% in recent months"
        else:
            report.activity_trend = "stable"
            report.activity_details = "Consistent activity level"
    elif len(commits_by_month) >= 1:
        report.activity_trend = "too early to determine"
        report.activity_details = f"Only {len(commits_by_month)} month(s) of data"

    # Weekend warrior detection
    total = analysis.total_commits
    weekend_commits = commits_by_weekday.get("Saturday", 0) + commits_by_weekday.get("Sunday", 0)
    report.weekend_commit_pct = (weekend_commits / total * 100) if total > 0 else 0
    report.is_weekend_warrior = report.weekend_commit_pct > 40

    # Night owl detection (10pm - 4am)
    night_commits = sum(commits_by_hour.get(h, 0) for h in [22, 23, 0, 1, 2, 3])
    report.night_commit_pct = (night_commits / total * 100) if total > 0 else 0
    report.is_night_owl = report.night_commit_pct > 25

    # Early bird detection (5am - 8am)
    morning_commits = sum(commits_by_hour.get(h, 0) for h in [5, 6, 7, 8])
    report.morning_commit_pct = (morning_commits / total * 100) if total > 0 else 0
    report.is_early_bird = report.morning_commit_pct > 20

    # Most active day and hour
    if commits_by_weekday:
        report.most_active_day = max(commits_by_weekday, key=commits_by_weekday.get)
    if commits_by_hour:
        report.most_active_hour = max(commits_by_hour, key=commits_by_hour.get)

    # Bus factor: how many contributors own >50% of commits
    report.bus_factor = _calculate_bus_factor(analysis.contributor_stats, total)
    if analysis.contributor_stats:
        report.bus_factor_contributors = [
            c["name"] for c in analysis.contributor_stats[:report.bus_factor]
        ]

    # Commits per week
    if analysis.first_commit_date and analysis.last_commit_date:
        span = analysis.last_commit_date - analysis.first_commit_date
        weeks = max(span.days / 7, 1)
        report.avg_commits_per_week = total / weeks
        report.commit_velocity = f"{total / max(analysis.active_days, 1):.1f} commits/active day"

        # Days since last commit
        now = datetime.now(analysis.last_commit_date.tzinfo)
        report.days_since_last_commit = (now - analysis.last_commit_date).days
        report.stale = report.days_since_last_commit > 90

    # Longest gap between commits
    if analysis.commits_by_day:
        days_sorted = sorted(analysis.commits_by_day.keys())
        max_gap = 0
        for i in range(1, len(days_sorted)):
            d1 = datetime.strptime(days_sorted[i - 1], "%Y-%m-%d")
            d2 = datetime.strptime(days_sorted[i], "%Y-%m-%d")
            gap = (d2 - d1).days
            if gap > max_gap:
                max_gap = gap
        report.longest_gap_days = max_gap

    # Seasonal pattern
    report.seasonal_pattern = _detect_seasonal(commits_by_month)

    return report


def _calculate_bus_factor(contributors: list, total_commits: int) -> int:
    """Calculate bus factor: minimum contributors covering >50% of commits."""
    if not contributors or total_commits == 0:
        return 0

    cumulative = 0
    for i, c in enumerate(contributors):
        cumulative += c["commits"]
        if cumulative > total_commits * 0.5:
            return i + 1
    return len(contributors)


def _detect_seasonal(commits_by_month: dict) -> str:
    """Detect seasonal patterns in commit activity."""
    if len(commits_by_month) < 6:
        return "insufficient data"

    # Group by calendar month
    month_totals = defaultdict(int)
    month_counts = defaultdict(int)
    for ym, count in commits_by_month.items():
        month_num = int(ym.split("-")[1])
        month_totals[month_num] += count
        month_counts[month_num] += 1

    month_avgs = {m: month_totals[m] / month_counts[m] for m in month_totals}
    if not month_avgs:
        return "no pattern detected"

    overall_avg = sum(month_avgs.values()) / len(month_avgs)
    if overall_avg == 0:
        return "no activity"

    # Find peak and trough seasons
    peak_months = [m for m, avg in month_avgs.items() if avg > overall_avg * 1.3]
    trough_months = [m for m, avg in month_avgs.items() if avg < overall_avg * 0.7]

    month_names = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }

    if peak_months and trough_months:
        peaks = ", ".join(month_names[m] for m in sorted(peak_months))
        troughs = ", ".join(month_names[m] for m in sorted(trough_months))
        return f"Peak: {peaks} | Low: {troughs}"
    elif peak_months:
        peaks = ", ".join(month_names[m] for m in sorted(peak_months))
        return f"Peak activity in {peaks}"
    else:
        return "no strong seasonal pattern"


def format_trend_report(report: TrendReport) -> str:
    """Format trend report for terminal output."""
    lines = []
    lines.append("=" * 60)
    lines.append("  TREND ANALYSIS")
    lines.append("=" * 60)

    # Activity trend
    trend_icon = {
        "increasing": "[UP]", "decreasing": "[DOWN]", "stable": "[STABLE]",
        "no activity": "[NONE]", "too early to determine": "[NEW]"
    }
    icon = trend_icon.get(report.activity_trend, "")
    lines.append(f"\n  Activity: {icon} {report.activity_trend.upper()}")
    if report.activity_details:
        lines.append(f"  {report.activity_details}")

    # Patterns
    lines.append(f"\n  Patterns:")
    if report.is_weekend_warrior:
        lines.append(f"    Weekend Warrior - {report.weekend_commit_pct:.1f}% of commits on weekends")
    if report.is_night_owl:
        lines.append(f"    Night Owl - {report.night_commit_pct:.1f}% of commits between 10pm-4am")
    if report.is_early_bird:
        lines.append(f"    Early Bird - {report.morning_commit_pct:.1f}% of commits between 5am-8am")
    if not (report.is_weekend_warrior or report.is_night_owl or report.is_early_bird):
        lines.append(f"    Standard work pattern")

    lines.append(f"    Most active day: {report.most_active_day}")
    lines.append(f"    Peak hour: {report.most_active_hour}:00")

    # Bus factor
    lines.append(f"\n  Bus Factor: {report.bus_factor}")
    if report.bus_factor == 1:
        lines.append(f"    WARNING: Single point of failure!")
        lines.append(f"    Key contributor: {report.bus_factor_contributors[0] if report.bus_factor_contributors else 'unknown'}")
    elif report.bus_factor <= 2:
        lines.append(f"    Low bus factor. Key contributors:")
        for name in report.bus_factor_contributors:
            lines.append(f"      - {name}")

    # Velocity
    if report.avg_commits_per_week > 0:
        lines.append(f"\n  Velocity:")
        lines.append(f"    {report.avg_commits_per_week:.1f} commits/week")
        lines.append(f"    {report.commit_velocity}")

    # Gaps and staleness
    if report.longest_gap_days > 0:
        lines.append(f"    Longest gap: {report.longest_gap_days} days")
    if report.days_since_last_commit > 0:
        lines.append(f"    Days since last commit: {report.days_since_last_commit}")
    if report.stale:
        lines.append(f"    STATUS: STALE (>90 days inactive)")

    # Seasonal
    if report.seasonal_pattern and report.seasonal_pattern != "insufficient data":
        lines.append(f"\n  Seasonal: {report.seasonal_pattern}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)
