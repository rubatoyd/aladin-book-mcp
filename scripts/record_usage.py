#!/usr/bin/env python3
"""Record traffic and release statistics for aladin-book-mcp repository."""

from __future__ import annotations
import csv
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OWNER = "rubatoyd"
REPO = "aladin-book-mcp"
DOCS_DIR = Path("docs")
CSV_PATH = DOCS_DIR / "usage.csv"
SVG_PATH = DOCS_DIR / "usage.svg"
README_PATH = Path("README.md")
HEADERS = ["date", "views", "clones", "stars", "releases_downloads"]


def gh_api(endpoint: str) -> dict:
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/{endpoint}"
    token = os.environ.get("GITHUB_TOKEN")
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "UsageTracker/1.0")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Warning: Failed to fetch {endpoint}: {e}")
        return {}


def get_traffic():
    views_data = gh_api("traffic/views")
    clones_data = gh_api("traffic/clones")
    repo_data = gh_api("")
    releases_data = gh_api("releases")

    views = views_data.get("count", 0)
    clones = clones_data.get("count", 0)
    stars = repo_data.get("stargazers_count", 0) if isinstance(repo_data, dict) else 0

    downloads = 0
    if isinstance(releases_data, list):
        for rel in releases_data:
            for asset in rel.get("assets", []):
                downloads += asset.get("download_count", 0)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return today, views, clones, stars, downloads


def generate_svg(rows: list[dict]):
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    dates = [r["date"] for r in rows][-14:]
    views = [int(r.get("views", 0)) for r in rows][-14:]
    downloads = [int(r.get("releases_downloads", 0)) for r in rows][-14:]

    if not dates:
        dates = [datetime.now(timezone.utc).strftime("%Y-%m-%d")]
        views = [0]
        downloads = [0]

    max_v = max(max(views), max(downloads), 10)
    width, height = 700, 260
    pad_left, pad_bottom, pad_top, pad_right = 60, 40, 40, 20
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    n = len(dates)
    pts_v = []
    pts_d = []
    for i, (v, d) in enumerate(zip(views, downloads)):
        x = pad_left + (i / max(1, n - 1)) * plot_w if n > 1 else pad_left + plot_w / 2
        y_v = pad_top + plot_h - (v / max_v) * plot_h
        y_d = pad_top + plot_h - (d / max_v) * plot_h
        pts_v.append((x, y_v))
        pts_d.append((x, y_d))

    poly_v = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts_v)
    poly_d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts_d)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#0d1117" rx="8"/>
  <text x="{width/2}" y="25" fill="#c9d1d9" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-size="14" font-weight="600" text-anchor="middle">Traffic &amp; Release Downloads (Last 14 Days)</text>
  <polyline fill="none" stroke="#58a6ff" stroke-width="2" points="{poly_v}"/>
  <polyline fill="none" stroke="#3fb950" stroke-width="2" points="{poly_d}"/>
  <circle cx="{width-180}" cy="22" r="5" fill="#58a6ff"/>
  <text x="{width-170}" y="26" fill="#8b949e" font-size="11" font-family="sans-serif">Views</text>
  <circle cx="{width-90}" cy="22" r="5" fill="#3fb950"/>
  <text x="{width-80}" y="26" fill="#8b949e" font-size="11" font-family="sans-serif">Downloads</text>
</svg>"""

    with open(SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg)


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    today, views, clones, stars, downloads = get_traffic()

    rows = []
    if CSV_PATH.exists():
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

    updated = False
    for r in rows:
        if r.get("date") == today:
            r["views"] = str(views)
            r["clones"] = str(clones)
            r["stars"] = str(stars)
            r["releases_downloads"] = str(downloads)
            updated = True
            break

    if not updated:
        rows.append({
            "date": today,
            "views": str(views),
            "clones": str(clones),
            "stars": str(stars),
            "releases_downloads": str(downloads),
        })

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    generate_svg(rows)
    print(f"Recorded usage for {today}: views={views}, clones={clones}, stars={stars}, downloads={downloads}")


if __name__ == "__main__":
    main()
