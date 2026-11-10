#!/usr/bin/env python3
"""Collect my commits across every repo I own and print an anonymized commits.json to stdout.

Each record is {p: project index, t: ISO timestamp, n: lines changed}. Repo names are dropped on
purpose so private projects are not exposed. Needs an authenticated `gh` with repo access.

  python3 scripts/fetch_commits.py > data/commits.json && python3 scripts/volume.py data/commits.json assets
"""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

USER = "AlvaroP100"

def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout else None

repos = sorted(r["name"] for r in gh("user/repos?per_page=100&affiliation=owner"))
commits = []
for i, repo in enumerate(repos):
    page = 1
    while True:
        batch = gh(f"repos/{USER}/{repo}/commits?per_page=100&page={page}&author={USER}")
        if not batch:
            break
        commits += [(i, repo, c["sha"], c["commit"]["author"]["date"]) for c in batch]
        if len(batch) < 100:
            break
        page += 1

def lines(c):
    s = (gh(f"repos/{USER}/{c[1]}/commits/{c[2]}") or {}).get("stats", {})
    return {"p": c[0], "t": c[3], "n": s.get("additions", 0) + s.get("deletions", 0)}

with ThreadPoolExecutor(8) as ex:
    out = list(ex.map(lines, commits))
json.dump(out, sys.stdout, separators=(",", ":"))
