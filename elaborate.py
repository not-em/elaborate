#!/usr/bin/env python3
"""
elaborate — look up a PyPI package without leaving the terminal.

Usage:
    elaborate pandas
    elaborate requests --deps
"""

import sys
import json
import gzip
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from textwrap import wrap as _wrap


def fetch_pypi(package: str) -> dict:
    url = f"https://pypi.org/pypi/{package}/json"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "Accept-Encoding": "gzip",  # Request compressed response
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
            # Decompress if server sent gzip
            if resp.headers.get("Content-Encoding") == "gzip":
                data = gzip.decompress(data)
            return json.loads(data)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            die(f'Package "{package}" not found on PyPI.')
        die(f"PyPI returned HTTP {e.code}.")
    except urllib.error.URLError:
        die("Could not reach PyPI. Check your connection.")


def parse_args():
    p = argparse.ArgumentParser(
        prog="elaborate",
        description="Look up a PyPI package without leaving the terminal.",
        add_help=True,
    )
    p.add_argument("package", help="Package name, e.g. pandas")
    p.add_argument("--deps", action="store_true", help="Show dependencies")
    p.add_argument("--no-color", action="store_true", help="Disable colour output")
    return p.parse_args()


# ── Colour helpers ────────────────────────────────────────────────────────────

USE_COLOR = True

# Pre-compute ANSI escape sequences
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[36m"
_WHITE = "\033[97m"
_RED = "\033[31m"

def bold(t):    return f"{_BOLD}{t}{_RESET}" if USE_COLOR else t
def dim(t):     return f"{_DIM}{t}{_RESET}" if USE_COLOR else t
def cyan(t):    return f"{_CYAN}{t}{_RESET}" if USE_COLOR else t
def white(t):   return f"{_WHITE}{t}{_RESET}" if USE_COLOR else t
def red(t):     return f"{_RED}{t}{_RESET}" if USE_COLOR else t


def die(msg):
    print(f"\n  {red('✗')} {msg}\n", file=sys.stderr)
    sys.exit(1)


# Pre-compute the rule string
_RULE = "─" * 60

def rule(width=60):
    return dim(_RULE) if width == 60 else dim("─" * width)


def fmt_date(iso: str) -> str:
    """Turn an ISO timestamp into something human-readable."""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        days = (datetime.now(timezone.utc) - dt).days
        if days == 0:
            return "today"
        if days == 1:
            return "yesterday"
        if days < 30:
            return f"{days} days ago"
        if days < 365:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        years = days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    except Exception:
        return iso[:10]


def wrap(text: str, width: int = 72, indent: int = 2) -> str:
    """Simple word wrapper using stdlib textwrap."""
    if not text:
        return ""
    prefix = " " * indent
    return "\n".join(_wrap(text, width=width, initial_indent=prefix, subsequent_indent=prefix))


def extract_github(project_urls: dict | None, home_page: str) -> str | None:
    """Try to find a GitHub URL from project URLs."""
    if project_urls:
        for val in project_urls.values():
            if val and "github.com" in val:
                return val.rstrip("/")
    if home_page and "github.com" in home_page:
        return home_page.rstrip("/")
    return None


def latest_upload_date(releases: dict, version: str) -> str:
    """Find the upload date of the latest release."""
    files = releases.get(version)
    if files:
        # Find max date in single pass without intermediate list
        max_date = None
        for f in files:
            d = f.get("upload_time_iso_8601")
            if d and (max_date is None or d > max_date):
                max_date = d
        if max_date:
            return fmt_date(max_date)
    return "unknown"


def print_result(data: dict, show_deps: bool):
    info = data["info"]
    releases = data.get("releases", {})

    # Cache all lookups upfront
    name = info.get("name", "")
    version = info.get("version", "")
    summary = info.get("summary") or ""
    license_ = info.get("license") or ""
    requires = info.get("requires_dist") or []
    project_urls = info.get("project_urls") or {}
    home_page = info.get("home_page") or ""
    requires_python = info.get("requires_python", "any")
    
    pypi_url = f"https://pypi.org/project/{name}"
    docs_url = info.get("docs_url") or project_urls.get("Documentation") or ""
    github_url = extract_github(project_urls, home_page)
    updated = latest_upload_date(releases, version)

    # Clean up license — sometimes it's a long SPDX blob
    if license_ and len(license_) > 40:
        license_ = license_[:40].split("\n", 1)[0].strip() + "…"

    # ── Build output ──────────────────────────────────────────────────────────
    lines = [
        "",
        f"  {bold(white(name))}  {dim('v' + version)}  {dim('·')}  {dim('updated ' + updated)}",
        f"  {rule()}",
    ]

    if summary:
        lines.append("")
        lines.append(wrap(summary, width=70, indent=2))

    lines.append("")
    if license_:
        lines.append(f"  {dim('License')}  {license_}")
    if requires:
        lines.append(f"  {dim('Requires')}  Python {requires_python}")

    lines.append("")
    lines.append(f"  {dim('Links')}")
    if docs_url:
        lines.append(f"    {dim('Docs      ')} {cyan(docs_url)}")
    if github_url:
        lines.append(f"    {dim('GitHub    ')} {cyan(github_url)}")
    lines.append(f"    {dim('PyPI      ')} {cyan(pypi_url)}")

    if show_deps:
        lines.append("")
        lines.append(f"  {dim('Dependencies')}")
        if requires:
            core = [r for r in requires if "; extra ==" not in r]
            optional_count = len(requires) - len(core)
            if core:
                dot = dim('·')
                for dep in core[:20]:
                    lines.append(f"    {dot} {dep}")
                if len(core) > 20:
                    lines.append(f"    {dim(f'… and {len(core) - 20} more')}")
            if optional_count:
                lines.append(f"    {dim(f'+ {optional_count} optional extras')}")
        else:
            lines.append(f"    {dim('none')}")

    lines.append("")
    lines.append(f"  {rule()}")
    lines.append("")

    # Single print call for all output
    print("\n".join(lines))


def main():
    global USE_COLOR
    args = parse_args()

    if args.no_color or not sys.stdout.isatty():
        USE_COLOR = False

    data = fetch_pypi(args.package)
    print_result(data, show_deps=args.deps)


if __name__ == "__main__":
    main()
