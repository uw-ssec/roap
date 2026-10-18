"""Migration gate: run_pipeline.sh drives the full pipeline end to end.

The plan asserted ``outputs/test/analysis_ready.csv`` with a ``verdict``
column holding 4 FAIL rows. None of those three facts hold:

* The final deliverable lands at ``<out>/oa_stage4_outputs/data/analysis_ready.csv``.
* The audit column is ``analysis_audit_status``, not ``verdict``.
* The generator injects 3 FAIL and 1 REVIEW (S005 REVIEW, S007/S010/S015
  FAIL) -- i.e. 4 *non-PASS* rows, not 4 FAIL rows.

This test asserts the generator's documented EXPECTED_STAGE4_OUTCOMES.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER = REPO_ROOT / "run_pipeline.sh"
EXAMPLE_XLSX = REPO_ROOT / "examples" / "example_data.xlsx"

FINAL_REL = Path("oa_stage4_outputs") / "data" / "analysis_ready.csv"

# From examples/make_example_data.py EXPECTED_STAGE4_OUTCOMES.
EXPECTED_FAIL = {"S007", "S010", "S015"}
EXPECTED_REVIEW = {"S005"}
EXPECTED_CRM_QC = {"RM213_1", "RM213_2", "RM213_3", "RM213_4"}
EXPECTED_STD_QC = {"TRIS_1", "TRIS_2", "TRIS_3"}
EXPECTED_NON_PASS = EXPECTED_FAIL | EXPECTED_REVIEW | EXPECTED_CRM_QC | EXPECTED_STD_QC


def test_run_pipeline_sh_exists() -> None:
    assert RUNNER.exists(), "run_pipeline.sh not migrated to repo root"


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable bit is not meaningful on Windows")
def test_run_pipeline_sh_executable() -> None:
    assert os.access(RUNNER, os.X_OK), "run_pipeline.sh not executable"


def test_run_pipeline_dry_run_succeeds(tmp_path: Path) -> None:
    """--dry-run resolves notebooks and prints the chain without executing."""
    if not shutil.which("bash"):
        pytest.skip("bash not available")

    result = subprocess.run(
        ["bash", str(RUNNER), str(EXAMPLE_XLSX), str(tmp_path / "out"), "--dry-run"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=300,
        env={**os.environ, "PYTHON_BIN": sys.executable},
    )
    assert result.returncode == 0, f"dry run failed:\n{result.stdout}\n{result.stderr}"


@pytest.mark.slow
def test_pipeline_runs_end_to_end(tmp_path: Path) -> None:
    """Full Papermill run produces the final deliverable with injected issues."""
    if not shutil.which("bash"):
        pytest.skip("bash not available")

    out_root = tmp_path / "out"
    result = subprocess.run(
        ["bash", str(RUNNER), str(EXAMPLE_XLSX), str(out_root)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=1800,
        env={**os.environ, "PYTHON_BIN": sys.executable},
    )
    assert result.returncode == 0, f"Pipeline failed:\n{result.stdout[-4000:]}\n{result.stderr[-4000:]}"

    final = out_root / FINAL_REL
    assert final.exists(), f"Missing final deliverable: {final}"

    df = pd.read_csv(final)
    assert len(df) == 27, f"Expected 20 sample rows, got {len(df)}"

    status = df.set_index("sample_tag")["analysis_audit_status"]
    non_pass = set(status[status != "PASS"].index)

    assert non_pass == EXPECTED_NON_PASS, (
        f"Expected non-PASS rows {sorted(EXPECTED_NON_PASS)}, got {sorted(non_pass)}. "
        f"Distribution: {status.value_counts().to_dict()}"
    )
    assert set(status[status == "FAIL"].index) == EXPECTED_FAIL
    assert set(status[status == "REVIEW"].index) == EXPECTED_REVIEW
