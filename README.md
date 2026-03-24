# Ghost Metrics

[![Built with Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-blue?logo=anthropic&logoColor=white)](https://claude.ai/code)


> Private, offline analytics for your GitHub repos. Zero data leaves your machine.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Stop sending your repo data to third-party analytics services.** Ghost Metrics parses your local git history and generates rich analytics dashboards — 100% offline.

## What You Get

- **Commit heatmap** (GitHub-style day x hour grid)
- **Contributor analysis** with bus factor detection
- **Activity trends** (increasing, decreasing, stable)
- **Code churn** (most frequently changed files)
- **Language distribution** by file extension
- **Pattern detection** (night owl, weekend warrior, early bird)
- **Interactive HTML reports** with Chart.js charts
- **Export** to JSON, CSV, Markdown, or HTML

## Install

```bash
pip install ghost-metrics
```

Or from source:

```bash
git clone https://github.com/ghost-metrics/ghost-metrics.git
cd ghost-metrics
pip install -e .
```

## Usage

```bash
# Quick analysis of current repo
ghost-metrics analyze

# Analyze a specific repo
ghost-metrics analyze --repo /path/to/repo

# Generate interactive HTML report
ghost-metrics report --repo .

# Detect trends and bus factor
ghost-metrics trends

# Contributor breakdown
ghost-metrics contributors

# Export data
ghost-metrics export --format json
ghost-metrics export --format csv --output data.csv
ghost-metrics export --format markdown
ghost-metrics export --format html --output report.html
```

## Sample Output

```
============================================================
  GHOST METRICS - my-project
============================================================

  Commits:      1,247
  Contributors: 8
  Lines Added:  +142,839
  Lines Deleted: -67,421
  Active Days:  312

  Top Languages:
    Python: 89 files
    JavaScript: 34 files
    TypeScript: 21 files

  Activity: [UP] INCREASING
  Bus Factor: 2
  Velocity: 12.3 commits/week
  Pattern: Night Owl (31% commits between 10pm-4am)
```

## Privacy

Ghost Metrics makes **zero network calls**. It only reads your local `.git` directory using `git log`. Your code, commit history, and contributor data never leave your machine.

## License

MIT
