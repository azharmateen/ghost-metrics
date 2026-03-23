"""Generate HTML report with Chart.js visualizations."""

import json
from datetime import datetime


def generate_html_report(analysis, trends) -> str:
    """Generate a complete HTML report with interactive charts."""
    # Prepare data for charts
    hours = list(range(24))
    hour_data = [analysis.commits_by_hour.get(h, 0) for h in hours]

    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_data = [analysis.commits_by_weekday.get(d, 0) for d in weekdays]

    months = sorted(analysis.commits_by_month.keys()) if analysis.commits_by_month else []
    month_data = [analysis.commits_by_month.get(m, 0) for m in months]

    # Language distribution (top 10)
    lang_items = sorted(analysis.language_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
    lang_labels = [l[0] for l in lang_items]
    lang_data = [l[1] for l in lang_items]

    # Contributor data (top 10)
    top_contributors = analysis.contributor_stats[:10]
    contrib_labels = [c["name"].split(" <")[0] for c in top_contributors]
    contrib_data = [c["commits"] for c in top_contributors]

    # Heatmap data
    heatmap_data = []
    for day_idx, day_name in enumerate(weekdays):
        if day_name in analysis.commit_heatmap:
            for hour in range(24):
                val = analysis.commit_heatmap[day_name].get(hour, 0)
                if val > 0:
                    heatmap_data.append({"x": hour, "y": day_idx, "v": val})

    # Activity sparkline (last 52 weeks of daily data)
    daily_dates = sorted(analysis.commits_by_day.keys())[-365:]
    daily_values = [analysis.commits_by_day.get(d, 0) for d in daily_dates]

    # Color palette
    colors = [
        "#4CAF50", "#2196F3", "#FF9800", "#E91E63", "#9C27B0",
        "#00BCD4", "#FF5722", "#795548", "#607D8B", "#CDDC39",
    ]

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ghost Metrics - {analysis.repo_name}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; padding: 24px; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
h1 {{ font-size: 2em; margin-bottom: 4px; color: #58a6ff; }}
.subtitle {{ color: #8b949e; margin-bottom: 24px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; margin-bottom: 24px; }}
.stat-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; }}
.stat-card .label {{ color: #8b949e; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px; }}
.stat-card .value {{ font-size: 1.8em; font-weight: 700; color: #f0f6fc; margin-top: 4px; }}
.stat-card .detail {{ color: #8b949e; font-size: 0.85em; margin-top: 4px; }}
.chart-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 16px; }}
.chart-card h3 {{ color: #f0f6fc; margin-bottom: 16px; }}
.chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }}
.heatmap {{ display: grid; grid-template-columns: 60px repeat(24, 1fr); gap: 2px; margin-top: 12px; }}
.heatmap-cell {{ aspect-ratio: 1; border-radius: 2px; min-height: 16px; }}
.heatmap-label {{ font-size: 0.7em; color: #8b949e; display: flex; align-items: center; }}
.heatmap-hour {{ font-size: 0.65em; color: #8b949e; text-align: center; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
th, td {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid #21262d; }}
th {{ color: #8b949e; font-size: 0.85em; text-transform: uppercase; }}
td {{ color: #c9d1d9; }}
.trend-badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }}
.trend-up {{ background: #1a3a1a; color: #3fb950; }}
.trend-down {{ background: #3d1a1a; color: #f85149; }}
.trend-stable {{ background: #1a2a3a; color: #58a6ff; }}
.footer {{ text-align: center; color: #484f58; margin-top: 32px; padding-top: 16px; border-top: 1px solid #21262d; font-size: 0.85em; }}
@media (max-width: 768px) {{ .chart-row {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="container">
    <h1>Ghost Metrics</h1>
    <p class="subtitle">{analysis.repo_name} &middot; Generated {now} &middot; 100% offline</p>

    <div class="grid">
        <div class="stat-card">
            <div class="label">Total Commits</div>
            <div class="value">{analysis.total_commits:,}</div>
            <div class="detail">{analysis.active_days} active days</div>
        </div>
        <div class="stat-card">
            <div class="label">Contributors</div>
            <div class="value">{analysis.total_contributors}</div>
            <div class="detail">Bus factor: {trends.bus_factor}</div>
        </div>
        <div class="stat-card">
            <div class="label">Lines Changed</div>
            <div class="value">{analysis.total_insertions + analysis.total_deletions:,}</div>
            <div class="detail">+{analysis.total_insertions:,} / -{analysis.total_deletions:,}</div>
        </div>
        <div class="stat-card">
            <div class="label">Activity Trend</div>
            <div class="value" style="font-size: 1.2em;">
                <span class="trend-badge trend-{'up' if trends.activity_trend == 'increasing' else 'down' if trends.activity_trend == 'decreasing' else 'stable'}">{trends.activity_trend.upper()}</span>
            </div>
            <div class="detail">{trends.activity_details}</div>
        </div>
        <div class="stat-card">
            <div class="label">Avg Commit Size</div>
            <div class="value">{analysis.avg_insertions + analysis.avg_deletions:.0f}</div>
            <div class="detail">lines/commit (+{analysis.avg_insertions:.0f} / -{analysis.avg_deletions:.0f})</div>
        </div>
        <div class="stat-card">
            <div class="label">Velocity</div>
            <div class="value">{trends.avg_commits_per_week:.1f}</div>
            <div class="detail">commits/week</div>
        </div>
    </div>

    <!-- Commit Heatmap (GitHub-style) -->
    <div class="chart-card">
        <h3>Commit Heatmap (Day x Hour)</h3>
        <div class="heatmap">
            <div></div>
            {"".join(f'<div class="heatmap-hour">{h}</div>' for h in range(24))}
            {"".join(_heatmap_row(day, analysis.commit_heatmap.get(day, {})) for day in weekdays)}
        </div>
    </div>

    <div class="chart-row">
        <div class="chart-card">
            <h3>Commits by Hour</h3>
            <canvas id="hourChart"></canvas>
        </div>
        <div class="chart-card">
            <h3>Commits by Day of Week</h3>
            <canvas id="weekdayChart"></canvas>
        </div>
    </div>

    <div class="chart-card">
        <h3>Monthly Activity</h3>
        <canvas id="monthChart" height="80"></canvas>
    </div>

    <div class="chart-row">
        <div class="chart-card">
            <h3>Top Contributors</h3>
            <canvas id="contribChart"></canvas>
        </div>
        <div class="chart-card">
            <h3>Language Distribution</h3>
            <canvas id="langChart"></canvas>
        </div>
    </div>

    <!-- Top Changed Files -->
    <div class="chart-card">
        <h3>Most Changed Files (Code Churn)</h3>
        <table>
            <tr><th>File</th><th>Changes</th></tr>
            {"".join(f'<tr><td>{f}</td><td>{c}</td></tr>' for f, c in analysis.top_changed_files[:15])}
        </table>
    </div>

    <!-- Contributors Table -->
    <div class="chart-card">
        <h3>Contributor Details</h3>
        <table>
            <tr><th>Name</th><th>Commits</th><th>Insertions</th><th>Deletions</th><th>Files Touched</th></tr>
            {"".join(f'<tr><td>{c["name"].split(" <")[0]}</td><td>{c["commits"]}</td><td>+{c["insertions"]:,}</td><td>-{c["deletions"]:,}</td><td>{c["files_touched"]}</td></tr>' for c in analysis.contributor_stats[:20])}
        </table>
    </div>

    <div class="footer">
        Ghost Metrics &middot; 100% offline, zero data leaves your machine &middot; ghostmetrics.dev
    </div>
</div>

<script>
const chartDefaults = {{
    color: '#8b949e',
    borderColor: '#30363d',
    font: {{ family: '-apple-system, BlinkMacSystemFont, sans-serif' }}
}};
Chart.defaults.color = chartDefaults.color;
Chart.defaults.borderColor = chartDefaults.borderColor;

// Hour chart
new Chart(document.getElementById('hourChart'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps([f"{h}:00" for h in hours])},
        datasets: [{{ label: 'Commits', data: {json.dumps(hour_data)}, backgroundColor: '#238636', borderRadius: 3 }}]
    }},
    options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true, grid: {{ color: '#21262d' }} }}, x: {{ grid: {{ display: false }} }} }} }}
}});

// Weekday chart
new Chart(document.getElementById('weekdayChart'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(weekdays)},
        datasets: [{{ label: 'Commits', data: {json.dumps(weekday_data)}, backgroundColor: '#1f6feb', borderRadius: 3 }}]
    }},
    options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true, grid: {{ color: '#21262d' }} }}, x: {{ grid: {{ display: false }} }} }} }}
}});

// Monthly chart
new Chart(document.getElementById('monthChart'), {{
    type: 'line',
    data: {{
        labels: {json.dumps(months)},
        datasets: [{{ label: 'Commits', data: {json.dumps(month_data)}, borderColor: '#58a6ff', backgroundColor: 'rgba(88,166,255,0.1)', fill: true, tension: 0.3 }}]
    }},
    options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true, grid: {{ color: '#21262d' }} }}, x: {{ grid: {{ display: false }} }} }} }}
}});

// Contributor pie
new Chart(document.getElementById('contribChart'), {{
    type: 'doughnut',
    data: {{
        labels: {json.dumps(contrib_labels)},
        datasets: [{{ data: {json.dumps(contrib_data)}, backgroundColor: {json.dumps(colors[:len(contrib_labels)])} }}]
    }},
    options: {{ plugins: {{ legend: {{ position: 'right', labels: {{ boxWidth: 12 }} }} }} }}
}});

// Language pie
new Chart(document.getElementById('langChart'), {{
    type: 'doughnut',
    data: {{
        labels: {json.dumps(lang_labels)},
        datasets: [{{ data: {json.dumps(lang_data)}, backgroundColor: {json.dumps(colors[:len(lang_labels)])} }}]
    }},
    options: {{ plugins: {{ legend: {{ position: 'right', labels: {{ boxWidth: 12 }} }} }} }}
}});
</script>
</body>
</html>"""
    return html


def _heatmap_row(day_name: str, hour_data: dict) -> str:
    """Generate one row of the heatmap."""
    max_val = max(hour_data.values()) if hour_data else 1
    cells = f'<div class="heatmap-label">{day_name[:3]}</div>'
    for h in range(24):
        val = hour_data.get(h, 0)
        if val == 0:
            color = "#161b22"
        else:
            intensity = min(val / max(max_val, 1), 1.0)
            if intensity < 0.25:
                color = "#0e4429"
            elif intensity < 0.5:
                color = "#006d32"
            elif intensity < 0.75:
                color = "#26a641"
            else:
                color = "#39d353"
        cells += f'<div class="heatmap-cell" style="background:{color}" title="{day_name} {h}:00 - {val} commits"></div>'
    return cells
