"""Migration gate: the prototype test suite must be fully present.

This test counts the suite via ``pytest --collect-only``, which *collects*
tests without executing them. That distinction matters: an earlier version
of this file shelled out to a full ``pytest`` run, which re-collected this
same file and spawned another full run, recursively forking the machine.
Collection-only is non-recursive and finishes in ~2s.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"

MIN_TESTS = 221
MIN_TEST_FILES = 14


def _collect_count() -> int:
    """Return the number of tests pytest can collect in this repo."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=300,
    )
    match = re.search(r"(\d+) tests? collected", result.stdout)
    assert match, (
        "Could not parse collection count from pytest output.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    return int(match.group(1))


def test_prototype_test_files_are_migrated() -> None:
    """All 14 prototype test modules are present in tests/."""
    test_files = sorted(p.name for p in TESTS_DIR.glob("test_*.py"))
    assert len(test_files) >= MIN_TEST_FILES, (
        f"Expected >={MIN_TEST_FILES} test files, found {len(test_files)}: {test_files}"
    )


def test_suite_collects_at_least_221_tests() -> None:
    """The migrated suite exposes at least the prototype's 221 tests."""
    count = _collect_count()
    assert count >= MIN_TESTS, f"Expected >={MIN_TESTS} tests collected, got {count}"
