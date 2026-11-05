#!/usr/bin/env python3
"""CalVer versions for the publish workflow (.github/workflows/publish.yml).

Releases are ``YYYY.0M.MICRO`` (see CHANGELOG.md), and the package version
comes from the ``vYYYY.0M.MICRO`` git tag through hatch-vcs (pyproject.toml).
Builds of ``main`` go to TestPyPI as a pre-release of the next release,
``YYYY.0M.MICRO.devN``, where N counts commits since the last tag.

    pixi run -e build python tools/release_version.py dev
    pixi run -e build python tools/release_version.py check-tag v2026.11.0
    pixi run -e build python tools/release_version.py check-dist v2026.11.0 dist

``dev`` prints the dev version; the publish workflow passes it to hatch-vcs as
``SETUPTOOLS_SCM_PRETEND_VERSION`` so dev builds roll over to the new month.
``check-tag`` fails unless the tag is ``vYYYY.0M.MICRO``. ``check-dist`` fails
unless every sdist and wheel in the directory carries the tag's version.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

from packaging.version import Version

CALVER_TAG = re.compile(r"^v(\d{4})\.(0[1-9]|1[0-2])\.(\d+)$")
DIST_NAME = re.compile(r"^roap-(?P<version>[^-]+?)(?:-py3-none-any\.whl|\.tar\.gz)$")


def next_release(today: dt.date, tags: list[str]) -> str:
    """The next CalVer release: this month's MICRO after any released this month."""
    month = f"{today.year}.{today.month:02d}"
    micros = [
        int(m.group(3))
        for m in map(CALVER_TAG.match, tags)
        if m and f"{m.group(1)}.{m.group(2)}" == month
    ]
    return f"{month}.{max(micros) + 1 if micros else 0}"


def dev_version(today: dt.date, tags: list[str], commits_since_tag: int) -> str:
    return f"{next_release(today, tags)}.dev{commits_since_tag}"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _commits_since_last_tag() -> int:
    try:
        last = _git("describe", "--tags", "--abbrev=0", "--match", "v*")
    except subprocess.CalledProcessError:  # no tags yet
        return int(_git("rev-list", "--count", "HEAD"))
    return int(_git("rev-list", "--count", f"{last}..HEAD"))


def check_tag(tag: str) -> None:
    if not CALVER_TAG.match(tag):
        raise SystemExit(f"tag {tag!r} is not a CalVer release tag (expected 'vYYYY.0M.MICRO')")


def check_dist(tag: str, dist: Path) -> list[str]:
    """Fail unless dist/ holds an sdist and a wheel, all versioned as the tag."""
    expected = Version(tag.removeprefix("v"))
    names = sorted(p.name for p in dist.iterdir() if p.suffix in {".whl", ".gz"})
    kinds = {name.endswith(".whl") for name in names}
    if kinds != {True, False}:
        raise SystemExit(f"expected one sdist and one wheel in {dist}, found {names}")
    for name in names:
        m = DIST_NAME.match(name)
        if not m or Version(m.group("version")) != expected:
            raise SystemExit(f"{name} is not version {expected} (tag {tag!r})")
    return names


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("dev", help="print the dev version for this commit")
    tag = sub.add_parser("check-tag", help="fail unless TAG is vYYYY.0M.MICRO")
    tag.add_argument("tag")
    dist = sub.add_parser("check-dist", help="fail unless DIST holds TAG's sdist and wheel")
    dist.add_argument("tag")
    dist.add_argument("dist", type=Path)
    args = parser.parse_args(argv)

    if args.command == "dev":
        version = dev_version(
            dt.datetime.now(dt.timezone.utc).date(),
            _git("tag", "--list", "v*").split(),
            _commits_since_last_tag(),
        )
        print(version)
    elif args.command == "check-tag":
        check_tag(args.tag)
        print(f"{args.tag} is a CalVer release tag")
    else:
        for name in check_dist(args.tag, args.dist):
            print(f"{name} matches {args.tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
