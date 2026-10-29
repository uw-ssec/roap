#!/usr/bin/env python3
"""CalVer versions for the publish workflow (.github/workflows/publish.yml).

Releases are ``YYYY.0M.MICRO`` (see CHANGELOG.md). Builds of ``main`` go to
TestPyPI as a pre-release of the next release, ``YYYY.0M.MICRO.devN``, where N
counts commits since the last tag.

    pixi run -e build python tools/release_version.py dev [--write]
    pixi run -e build python tools/release_version.py check-tag v2026.11.0

``dev`` prints the dev version; ``--write`` also stamps it into
pyproject.toml (CI only; the committed file keeps the release version).
``check-tag`` fails unless the tag is ``v`` + the pyproject.toml version.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
CALVER_TAG = re.compile(r"^v(\d{4})\.(\d{2})\.(\d+)$")
VERSION_LINE = re.compile(r'^version = "[^"]*"$', re.MULTILINE)


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


def pyproject_version(path: Path = PYPROJECT) -> str:
    with path.open("rb") as f:
        return tomllib.load(f)["project"]["version"]


def write_version(version: str, path: Path = PYPROJECT) -> None:
    text = path.read_text(encoding="utf-8")
    new, count = VERSION_LINE.subn(f'version = "{version}"', text, count=1)
    if count != 1:
        raise SystemExit(f"no 'version = \"...\"' line in {path}")
    path.write_text(new, encoding="utf-8")
    if pyproject_version(path) != version:
        raise SystemExit(f"stamped the wrong version line in {path}")


def check_tag(tag: str, version: str) -> None:
    if tag != f"v{version}":
        raise SystemExit(
            f"tag {tag!r} does not match pyproject.toml version {version!r} "
            f"(expected 'v{version}')"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    dev = sub.add_parser("dev", help="print the dev version for this commit")
    dev.add_argument("--write", action="store_true", help="stamp it into pyproject.toml")
    tag = sub.add_parser("check-tag", help="fail unless TAG == v<pyproject version>")
    tag.add_argument("tag")
    args = parser.parse_args(argv)

    if args.command == "dev":
        version = dev_version(
            dt.datetime.now(dt.timezone.utc).date(),
            _git("tag", "--list", "v*").split(),
            _commits_since_last_tag(),
        )
        if args.write:
            write_version(version)
        print(version)
    else:
        check_tag(args.tag, pyproject_version())
        print(f"{args.tag} matches pyproject.toml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
