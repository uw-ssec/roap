"""Migration gate: the prototype test suite must be fully present.

Counting is scoped to the 14 prototype-derived files **by name**, not to the
whole suite. Scoping matters: P1-04..P1-12 added 80+ tests of their own, so a
whole-suite ``>= 221`` threshold carried enough slack that deleting an entire
migrated module (test_schema.py, 70 tests) still passed. Per-file expectations
make any deletion or mass-skip fail loudly.

Counting uses ``pytest --collect-only``, which collects without executing. An
earlier version shelled out to a full ``pytest`` run, which re-collected this
same file and spawned another full run, recursively forking the machine.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"
PROTOTYPE_TESTS_DIR = REPO_ROOT / "references" / "prototype" / "oa_pipeline" / "tests"

# Measured per-file collection counts for the migrated prototype suite.
# test_carbonate_calc.py collects 0 if PyCO2SYS is missing, which is exactly
# the silent-zero this mapping exists to catch.
EXPECTED_COUNTS = {
    "test_app_core.py": 15,
    "test_carbonate_calc.py": 8,
    "test_coalesce.py": 16,
    "test_common.py": 16,
    "test_inspect.py": 10,
    "test_pipeline_e2e.py": 19,
    "test_policy.py": 5,
    "test_qc_ta_ph.py": 14,
    "test_readiness.py": 25,
    "test_schema.py": 70,
    "test_stage1b.py": 9,
    "test_stage2.py": 5,
    "test_stage3.py": 8,
    "test_stage4.py": 9,
}

# 221 is the prototype's documented test count; it is the sum above minus the
# 8 carbonate tests, which only collect when PyCO2SYS is installed.
PROTOTYPE_DOCUMENTED_COUNT = 221


def _collect_count(target: str) -> int:
    """Number of tests pytest collects for a path, without executing them."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", target],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=300,
    )
    match = re.search(r"(\d+) tests? collected", result.stdout)
    if not match:
        if "no tests collected" in result.stdout.lower():
            return 0
        pytest.fail(
            f"Could not parse collection count for {target}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return int(match.group(1))


def test_every_prototype_test_file_was_migrated() -> None:
    """Each test module in the prototype has a counterpart in tests/."""
    expected = sorted(p.name for p in PROTOTYPE_TESTS_DIR.glob("test_*.py"))
    missing = [name for name in expected if not (TESTS_DIR / name).exists()]
    assert not missing, f"Prototype test files not migrated: {missing}"


def test_expected_counts_cover_every_prototype_file() -> None:
    """EXPECTED_COUNTS stays in sync with the prototype as it changes."""
    actual = sorted(p.name for p in PROTOTYPE_TESTS_DIR.glob("test_*.py"))
    assert sorted(EXPECTED_COUNTS) == actual, (
        "EXPECTED_COUNTS is out of sync with the prototype test files. "
        f"Prototype has {actual}; mapping has {sorted(EXPECTED_COUNTS)}"
    )


@pytest.mark.parametrize("fname,expected", sorted(EXPECTED_COUNTS.items()))
def test_migrated_file_collects_expected_tests(fname: str, expected: int) -> None:
    """Each migrated file still collects its full set of tests.

    An exact match (not >=) catches both deletion and silent module-level
    skips, e.g. a missing optional dependency collapsing a file to zero.
    """
    count = _collect_count(f"tests/{fname}")
    assert count == expected, (
        f"{fname} collects {count} tests, expected {expected}. "
        "A drop usually means tests were deleted or a module-level "
        "importorskip collapsed the file to zero."
    )


def test_prototype_total_meets_documented_count() -> None:
    """The migrated files together meet the prototype's documented 221."""
    total = sum(_collect_count(f"tests/{f}") for f in EXPECTED_COUNTS)
    assert total >= PROTOTYPE_DOCUMENTED_COUNT, (
        f"Migrated prototype files collect {total} tests, "
        f"expected >={PROTOTYPE_DOCUMENTED_COUNT}"
    )
