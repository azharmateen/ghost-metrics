"""Ghost Metrics CLI - Private, offline analytics for your Git repos."""

import os
import sys
import click

from ghost_metrics.collector import collect_repo
from ghost_metrics.analyzer import analyze_repo
from ghost_metrics.trends import detect_trends, format_trend_report
from ghost_metrics.visualizer import generate_html_report
from ghost_metrics.exporter import export_json, export_csv, export_markdown, save_export


@click.group()
@click.version_option(version="1.0.0", prog_name="ghost-metrics")
def cli():
    """Ghost Metrics - Private, offline analytics for your Git repos.

    All data stays on your machine. Zero network calls. Pure git log parsing.
    """
    pass


@cli.command()
@click.option("--repo", "-r", default=".", help="Path to git repository (default: current dir)")
@click.option("--max-commits", "-n", default=10000, help="Maximum commits to analyze")
def analyze(repo, max_commits):
    """Analyze a git repository and display summary."""
    repo = os.path.abspath(repo)
    if not os.path.isdir(os.path.join(repo, ".git")):
        click.echo(f"Error: {repo} is not a git repository", err=True)
        sys.exit(1)

    click.echo(f"Collecting data from {repo}...")
    repo_data = collect_repo(repo, max_commits)

    click.echo(f"Analyzing {len(repo_data.commits)} commits...")
    analysis = analyze_repo(repo_data)

    click.echo()
    click.echo("=" * 60)
    click.echo(f"  GHOST METRICS - {analysis.repo_name}")
    click.echo("=" * 60)
    click.echo()
    click.echo(f"  Commits:      {analysis.total_commits:,}")
    click.echo(f"  Contributors: {analysis.total_contributors}")
    click.echo(f"  Lines Added:  +{analysis.total_insertions:,}")
    click.echo(f"  Lines Deleted: -{analysis.total_deletions:,}")
    click.echo(f"  Active Days:  {analysis.active_days}")
    click.echo(f"  Files in Repo: {repo_data.total_files}")
    click.echo(f"  Branches:     {len(repo_data.branches)}")
    click.echo(f"  Tags:         {len(repo_data.tags)}")

    if analysis.first_commit_date:
        click.echo(f"\n  First Commit: {analysis.first_commit_date.strftime('%Y-%m-%d %H:%M')}")
    if analysis.last_commit_date:
        click.echo(f"  Last Commit:  {analysis.last_commit_date.strftime('%Y-%m-%d %H:%M')}")

    click.echo(f"\n  Avg Commit Size: {analysis.avg_commit_size:.1f} files, {analysis.avg_insertions + analysis.avg_deletions:.0f} lines")

    # Top 5 languages
    if analysis.language_distribution:
        click.echo(f"\n  Top Languages:")
        for lang, count in list(analysis.language_distribution.items())[:5]:
            click.echo(f"    {lang}: {count} files")

    # Top 5 contributors
    if analysis.contributor_stats:
        click.echo(f"\n  Top Contributors:")
        for c in analysis.contributor_stats[:5]:
            name = c["name"].split(" <")[0]
            click.echo(f"    {name}: {c['commits']} commits (+{c['insertions']:,}/-{c['deletions']:,})")

    # Top changed files
    if analysis.top_changed_files:
        click.echo(f"\n  Most Changed Files:")
        for f, count in analysis.top_changed_files[:5]:
            click.echo(f"    {f}: {count} changes")

    click.echo("\n" + "=" * 60)


@cli.command()
@click.option("--repo", "-r", default=".", help="Path to git repository")
@click.option("--output", "-o", default=None, help="Output HTML file path")
@click.option("--max-commits", "-n", default=10000, help="Maximum commits to analyze")
def report(repo, output, max_commits):
    """Generate an interactive HTML report with charts."""
    repo = os.path.abspath(repo)
    if not os.path.isdir(os.path.join(repo, ".git")):
        click.echo(f"Error: {repo} is not a git repository", err=True)
        sys.exit(1)

    click.echo(f"Collecting data from {repo}...")
    repo_data = collect_repo(repo, max_commits)

    click.echo(f"Analyzing {len(repo_data.commits)} commits...")
    analysis = analyze_repo(repo_data)
    trend_report = detect_trends(analysis)

    click.echo("Generating HTML report...")
    html = generate_html_report(analysis, trend_report)

    if output is None:
        output = f"ghost-metrics-{analysis.repo_name}.html"

    filepath = save_export(html, output)
    click.echo(f"Report saved to: {filepath}")
    click.echo("Open in your browser to view interactive charts.")


@cli.command()
@click.option("--repo", "-r", default=".", help="Path to git repository")
@click.option("--max-commits", "-n", default=10000, help="Maximum commits to analyze")
def trends(repo, max_commits):
    """Detect activity trends, patterns, and bus factor."""
    repo = os.path.abspath(repo)
    if not os.path.isdir(os.path.join(repo, ".git")):
        click.echo(f"Error: {repo} is not a git repository", err=True)
        sys.exit(1)

    click.echo(f"Analyzing trends for {repo}...")
    repo_data = collect_repo(repo, max_commits)
    analysis = analyze_repo(repo_data)
    trend_report = detect_trends(analysis)

    click.echo(format_trend_report(trend_report))


@cli.command()
@click.option("--repo", "-r", default=".", help="Path to git repository")
@click.option("--max-commits", "-n", default=10000, help="Maximum commits to analyze")
def contributors(repo, max_commits):
    """Show detailed contributor statistics."""
    repo = os.path.abspath(repo)
    if not os.path.isdir(os.path.join(repo, ".git")):
        click.echo(f"Error: {repo} is not a git repository", err=True)
        sys.exit(1)

    click.echo(f"Analyzing contributors for {repo}...")
    repo_data = collect_repo(repo, max_commits)
    analysis = analyze_repo(repo_data)

    click.echo()
    click.echo("=" * 80)
    click.echo("  CONTRIBUTORS")
    click.echo("=" * 80)
    click.echo()

    header = f"  {'Name':<30} {'Commits':>8} {'Added':>10} {'Deleted':>10} {'Files':>6}"
    click.echo(header)
    click.echo("  " + "-" * 76)

    for c in analysis.contributor_stats:
        name = c["name"].split(" <")[0][:28]
        click.echo(f"  {name:<30} {c['commits']:>8} {'+' + str(c['insertions']):>10} {'-' + str(c['deletions']):>10} {c['files_touched']:>6}")

    click.echo()
    click.echo(f"  Total: {analysis.total_contributors} contributors")

    # Bus factor
    trend_report = detect_trends(analysis)
    click.echo(f"  Bus Factor: {trend_report.bus_factor}")
    if trend_report.bus_factor == 1:
        click.echo("  WARNING: Single point of failure!")
    click.echo()


@cli.command()
@click.option("--repo", "-r", default=".", help="Path to git repository")
@click.option("--format", "-f", "fmt", type=click.Choice(["json", "csv", "markdown", "html"]), default="json", help="Export format")
@click.option("--output", "-o", default=None, help="Output file path")
@click.option("--max-commits", "-n", default=10000, help="Maximum commits to analyze")
def export(repo, fmt, output, max_commits):
    """Export analytics data in various formats."""
    repo = os.path.abspath(repo)
    if not os.path.isdir(os.path.join(repo, ".git")):
        click.echo(f"Error: {repo} is not a git repository", err=True)
        sys.exit(1)

    click.echo(f"Collecting and analyzing {repo}...")
    repo_data = collect_repo(repo, max_commits)
    analysis = analyze_repo(repo_data)
    trend_report = detect_trends(analysis)

    ext_map = {"json": ".json", "csv": ".csv", "markdown": ".md", "html": ".html"}

    if fmt == "json":
        content = export_json(analysis, trend_report)
    elif fmt == "csv":
        content = export_csv(analysis)
    elif fmt == "markdown":
        content = export_markdown(analysis, trend_report)
    elif fmt == "html":
        from ghost_metrics.visualizer import generate_html_report
        content = generate_html_report(analysis, trend_report)

    if output is None:
        output = f"ghost-metrics-{analysis.repo_name}{ext_map[fmt]}"

    filepath = save_export(content, output)
    click.echo(f"Exported to: {filepath}")


if __name__ == "__main__":
    cli()
