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


def gh_api(endpoint: str = "") -> dict | list:
    url = f"https://api.github.com/repos/{OWNER}/{REPO}"
    if endpoint:
        url = f"{url}/{endpoint.lstrip('/')}"
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

    views = views_data.get("count", 0) if isinstance(views_data, dict) else 0
    clones = clones_data.get("count", 0) if isinstance(clones_data, dict) else 0
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
    recent = rows[-14:] if len(rows) >= 14 else rows
    
    dates = [r["date"] for r in recent]
    views = [int(r.get("views", 0)) for r in recent]
    downloads = [int(r.get("releases_downloads", 0)) for r in recent]

    if not dates:
        dates = [datetime.now(timezone.utc).strftime("%Y-%m-%d")]
        views = [0]
        downloads = [0]

    max_val = max(max(views), max(downloads), 5)
    # round max_val up to nice interval
    if max_val <= 5:
        y_max = 5
        y_ticks = [0, 2, 5]
    elif max_val <= 10:
        y_max = 10
        y_ticks = [0, 5, 10]
    else:
        y_max = ((max_val + 9) // 10) * 10
        y_ticks = [0, y_max // 2, y_max]

    width, height = 700, 260
    pad_left, pad_bottom, pad_top, pad_right = 55, 45, 45, 25
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    n = len(dates)
    pts_v = []
    pts_d = []
    
    for i, (v, d) in enumerate(zip(views, downloads)):
        x = pad_left + (i / max(1, n - 1)) * plot_w if n > 1 else pad_left + plot_w / 2
        y_v = pad_top + plot_h - (v / y_max) * plot_h
        y_d = pad_top + plot_h - (d / y_max) * plot_h
        pts_v.append((x, y_v, v, dates[i]))
        pts_d.append((x, y_d, d, dates[i]))

    # SVG Elements
    grid_lines = []
    for val in y_ticks:
        y = pad_top + plot_h - (val / y_max) * plot_h
        grid_lines.append(f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - pad_right}" y2="{y:.1f}" stroke="#21262d" stroke-dasharray="3,3"/>')
        grid_lines.append(f'<text x="{pad_left - 10}" y="{y + 4:.1f}" fill="#8b949e" font-size="11" font-family="-apple-system,sans-serif" text-anchor="end">{val}</text>')

    x_labels = []
    # show first, middle, and last date if multiple
    label_indices = [0, n - 1] if n > 1 else [0]
    if n > 4:
        label_indices.insert(1, n // 2)
    for idx in sorted(set(label_indices)):
        x, _, _, dt = pts_v[idx]
        short_dt = dt[5:] if len(dt) >= 10 else dt
        x_labels.append(f'<text x="{x:.1f}" y="{height - 15}" fill="#8b949e" font-size="11" font-family="-apple-system,sans-serif" text-anchor="middle">{short_dt}</text>')

    poly_v = " ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in pts_v)
    poly_d = " ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in pts_d)

    circles_v = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#58a6ff"><title>Views ({dt}): {val}</title></circle>' for x, y, val, dt in pts_v)
    circles_d = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#3fb950"><title>Downloads ({dt}): {val}</title></circle>' for x, y, val, dt in pts_d)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#0d1117" rx="8" stroke="#30363d" stroke-width="1"/>
  <text x="{pad_left}" y="28" fill="#e6edf3" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-size="13" font-weight="600">Traffic &amp; Release Downloads (Last 14 Days)</text>
  
  <!-- Legend -->
  <circle cx="{width-180}" cy="24" r="4.5" fill="#58a6ff"/>
  <text x="{width-170}" y="28" fill="#8b949e" font-size="11" font-family="-apple-system,sans-serif">Views</text>
  <circle cx="{width-90}" cy="24" r="4.5" fill="#3fb950"/>
  <text x="{width-80}" y="28" fill="#8b949e" font-size="11" font-family="-apple-system,sans-serif">Downloads</text>

  <!-- Grid & Ticks -->
  {"".join(grid_lines)}
  {"".join(x_labels)}

  <!-- Lines -->
  {f'<polyline fill="none" stroke="#58a6ff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" points="{poly_v}"/>' if n > 1 else ''}
  {f'<polyline fill="none" stroke="#3fb950" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" points="{poly_d}"/>' if n > 1 else ''}

  <!-- Points -->
  {circles_v}
  {circles_d}
</svg>"""

    with open(SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg)


def update_readme_stats(views: int, clones: int, downloads: int):
    if not README_PATH.exists():
        return
    content = README_PATH.read_text(encoding="utf-8")
    new_stats = f"> 📊 **사용량 통계** — 최근 14일 조회 **{views:,}**회 · 클론 **{clones:,}**회 · 릴리스 다운로드 **{downloads:,}**건  \n> ![Usage Graph](docs/usage.svg)"
    pattern = r"<!-- usage:start -->[\s\S]*?<!-- usage:end -->"
    replacement = f"<!-- usage:start -->\n{new_stats}\n<!-- usage:end -->"
    if re.search(pattern, content):
        updated = re.sub(pattern, replacement, content)
        README_PATH.write_text(updated, encoding="utf-8")


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
    update_readme_stats(views, clones, downloads)
    print(f"Recorded usage for {today}: views={views}, clones={clones}, stars={stars}, downloads={downloads}")


if __name__ == "__main__":
    main()
