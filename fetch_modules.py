#!/usr/bin/env python3
"""Fetch official NUS module info from NUSMods into raw/nusmods/.

Reads my-modules.md (one module code per line), calls the free, no-auth NUSMods
API for each, and writes a readable markdown file per module into raw/nusmods/.
Those become normal raw sources, which the /module command then turns into wiki
project pages that combine the official scaffold with links to your own notes.

Usage:
    ./env/bin/python fetch_modules.py
"""

import os
import re
import sys
import json
import time
import datetime
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
MODULES_LIST = os.path.join(HERE, "my-modules.md")
OUT_DIR = os.path.join(HERE, "raw", "nusmods")

# Latest live academic year first; the fetcher falls back through these if a
# module isn't offered in the preferred year.
ACAD_YEARS = ["2025-2026", "2024-2025", "2023-2024"]
API = "https://api.nusmods.com/v2/{year}/modules/{code}.json"

# NUSMods returns workload as [lecture, tutorial, lab, project, preparation]
# hours per week.
WORKLOAD_LABELS = ["Lectures", "Tutorials", "Laboratory", "Project / assignments", "Preparation"]


def parse_module_list(path):
    """Return a list of (code, pinned_year_or_None) from my-modules.md."""
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            year = None
            if "@" in line:
                code, _, year = (p.strip() for p in line.partition("@"))
            else:
                code = line
            code = code.upper().split()[0] if code.split() else code.upper()
            if re.match(r"^[A-Z]{1,4}\d{4}[A-Z]?$", code):
                entries.append((code, year or None))
            else:
                print(f"  skipped (not a module code): {line!r}")
    return entries


def fetch_module(code, pinned_year):
    """Fetch one module's JSON, trying the pinned year then the fallbacks."""
    years = [pinned_year] if pinned_year else ACAD_YEARS
    last_err = None
    for year in years:
        url = API.format(year=year, code=code)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "second-brain-fetch"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8")), year, url
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}"
            if e.code == 404:
                continue  # not offered that year, try next
            break
        except Exception as e:
            last_err = str(e)
            break
    raise RuntimeError(last_err or "unknown error")


def workload_lines(workload):
    if not isinstance(workload, list):
        return []
    out = []
    for label, hours in zip(WORKLOAD_LABELS, workload):
        if hours:
            out.append(f"- {label}: {hours} hrs/week")
    return out


def semesters_offered(data):
    sems = []
    for s in data.get("semesterData", []) or []:
        n = s.get("semester")
        if n:
            sems.append(f"Semester {n}")
    return ", ".join(sems) if sems else "Not listed"


def to_markdown(data, year, url):
    code = data.get("moduleCode", "")
    title = data.get("title", "")
    lines = [f"# {code} — {title}", ""]
    lines.append(f"> Source: NUSMods {year} — {url}")
    lines.append(f"> Fetched: {datetime.date.today().isoformat()}")
    lines.append("")
    lines.append(f"- Module credits: {data.get('moduleCredit', '?')}")
    lines.append(f"- Faculty / department: {data.get('faculty', '?')} / {data.get('department', '?')}")
    lines.append(f"- Offered: {semesters_offered(data)}")
    grading = data.get("gradingBasisDescription")
    if grading:
        lines.append(f"- Grading: {grading}")
    lines.append("")

    desc = (data.get("description") or "").strip()
    if desc:
        lines += ["## Description", "", desc, ""]

    wl = workload_lines(data.get("workload"))
    if wl:
        lines += ["## Workload (hours per week)", ""] + wl + [""]

    prereq = (data.get("prerequisite") or "").strip()
    if prereq:
        lines += ["## Prerequisites", "", prereq, ""]

    precl = (data.get("preclusion") or "").strip()
    if precl:
        lines += ["## Preclusions", "", precl, ""]

    extra = (data.get("additionalInformation") or "").strip()
    if extra:
        lines += ["## Additional information", "", extra, ""]

    return "\n".join(lines).rstrip() + "\n"


def main():
    entries = parse_module_list(MODULES_LIST)
    if not entries:
        print(f"No modules found in {MODULES_LIST}.")
        print("Add module codes (one per line), then run this again.")
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Fetching {len(entries)} module(s) from NUSMods...")
    ok, failed = [], []
    for code, pinned in entries:
        try:
            data, year, url = fetch_module(code, pinned)
            dest = os.path.join(OUT_DIR, f"{code}.md")
            with open(dest, "w", encoding="utf-8") as f:
                f.write(to_markdown(data, year, url))
            ok.append(code)
            print(f"  ✓ {code} ({year}) → raw/nusmods/{code}.md")
        except Exception as e:
            failed.append(code)
            print(f"  ✗ {code}: {e}")
        time.sleep(0.3)  # be polite to the API

    print(f"\nDone. {len(ok)} fetched, {len(failed)} failed.")
    if ok:
        print("Next: run /module to build the wiki project pages.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
