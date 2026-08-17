#!/usr/bin/env python3
"""Check PyPI for newer releases of the DX dependencies the overlay installs.

Run by `.github/workflows/dx-dependencies.yml` every two weeks. Standard library only,
so it needs no environment beyond CPython.

    python scripts/bump_dev_requirements.py --check   # exit 1 when something is stale
    python scripts/bump_dev_requirements.py           # rewrite the pins, print a summary

Pins stay exact (`==`). Loosening them to `>=` would make regeneration of the golden
example depend on the day it runs, which is the failure mode this file exists to prevent.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

REQUIREMENTS = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "django_ai_harness"
    / "data"
    / "dev-requirements.txt"
)
PYPI = "https://pypi.org/pypi/{name}/json"
TIMEOUT = 30
USER_AGENT = "django-ai-harness-dependency-bot"


def latest_version(name: str) -> str | None:
    """Return the newest non-yanked stable release, or None when PyPI is unreachable."""
    request = urllib.request.Request(  # noqa: S310 - fixed https host
        PYPI.format(name=name),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:  # noqa: S310
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"warning: could not query {name}: {exc}", file=sys.stderr)
        return None

    version = payload["info"]["version"]
    files = payload.get("releases", {}).get(version, [])
    if files and all(item.get("yanked") for item in files):
        print(f"warning: {name} {version} is yanked, keeping the current pin", file=sys.stderr)
        return None
    return version


def parse(text: str) -> list[tuple[int, str, str]]:
    """Return ``(line_index, name, version)`` for every pinned requirement."""
    entries = []
    for index, raw in enumerate(text.splitlines()):
        line = raw.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, _, version = line.partition("==")
        entries.append((index, name.strip(), version.strip()))
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report outdated pins and exit 1 without writing.",
    )
    args = parser.parse_args()

    text = REQUIREMENTS.read_text(encoding="utf-8")
    lines = text.splitlines()
    updates: list[str] = []

    for index, name, current in parse(text):
        latest = latest_version(name)
        if latest is None or latest == current:
            continue
        updates.append(f"- `{name}` {current} → {latest}")
        lines[index] = f"{name}=={latest}"

    if not updates:
        print("All DX dependencies are up to date.")
        return 0

    print("Outdated DX dependencies:")
    for update in updates:
        print(f"  {update}")

    if args.check:
        return 1

    REQUIREMENTS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = Path("dependency-updates.md")
    summary.write_text("\n".join(updates) + "\n", encoding="utf-8")
    print(f"\nUpdated {REQUIREMENTS.relative_to(Path.cwd())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
