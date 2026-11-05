"""Migration gate: the pipeline runs end to end and run_pipeline.sh is usable.

The plan asserted ``outputs/test/analysis_ready.csv`` with a ``verdict``
column holding 4 FAIL rows. None of those three facts hold:

* The final deliverable lands at ``<out>/oa_stage4_outputs/data/analysis_ready.csv``.
* The audit column is ``analysis_audit_status``, not ``verdict``.
* The generator injects 3 FAIL and 1 REVIEW (S005 REVIEW, S007/S010/S015
  FAIL) -- i.e. 4 *non-PASS* rows, not 4 FAIL rows.

This test asserts the generator's documented EXPECTED_STAGE4_OUTCOMES.
"""

import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from roap.pipeline import run_pipeline

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


def test_run_pipeline_dry_run_succeeds(tmp_path: Path, bash_exe: str) -> None:
    """--dry-run parses the arguments and prints the roap run command without executing."""
    result = subprocess.run(
        [bash_exe, RUNNER.as_posix(), EXAMPLE_XLSX.as_posix(), (tmp_path / "out").as_posix(), "--dry-run"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=300,
        env={**os.environ, "PYTHON_BIN": sys.executable},
    )
    assert result.returncode == 0, f"dry run failed:\n{result.stdout}\n{result.stderr}"


@pytest.mark.slow
def test_pipeline_runs_end_to_end(tmp_path: Path) -> None:
    """A full in-process run produces the final deliverable with injected issues.

    run_pipeline.sh's own end to end smoke test is test_run_pipeline_sh.py.
    """
    out_root = tmp_path / "out"
    run_pipeline(EXAMPLE_XLSX, out_root, runs_dir=out_root / "runs" / "test", log=lambda _: None)

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


def test_qc_config_sheet_wins_over_caller_sheet(tmp_path: Path) -> None:
    """A QC config's SHEET selects the sheet, as in notebook 02 (file over caller).

    The workbook's first sheet is a decoy with fewer Sample rows. With
    ``parameters: {SHEET: 1}`` and the default ``sheet=0``, the QC read, the
    manifest and the Stage 1A handoff must all use the second sheet, even
    when the decoy's QC outputs are also present under the output root.
    """
    import json
    import shutil

    real = pd.read_excel(EXAMPLE_XLSX, sheet_name=0)
    decoy = real[~real["sample_tag"].isin({"S001", "S002", "S003"})]
    workbook = tmp_path / "two_sheets.xlsx"
    with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
        decoy.to_excel(writer, sheet_name="decoy", index=False)
        real.to_excel(writer, sheet_name="real", index=False)

    out_root = tmp_path / "out"
    quiet = {"log": lambda _: None}
    # Leave the decoy's QC outputs in place, so the handoff has two sheets to choose from.
    run_pipeline(workbook, out_root, runs_dir=out_root / "runs" / "decoy", **quiet)
    assert len(pd.read_csv(out_root / FINAL_REL)) == 24

    cfg_dir = tmp_path / "configs"
    cfg_dir.mkdir()
    shutil.copy(REPO_ROOT / "configs" / "crm_certified_values.yaml", cfg_dir)
    (cfg_dir / "02_ta_ph_qc.yaml").write_text("parameters:\n  SHEET: 1\n", encoding="utf-8")

    run_pipeline(workbook, out_root, cfg_dir, runs_dir=out_root / "runs" / "real", **quiet)
    assert len(pd.read_csv(out_root / FINAL_REL)) == 27

    qc_out = out_root / "oa_prelim_data__qc_outputs"
    manifests = [json.loads(p.read_text(encoding="utf-8")) for p in qc_out.rglob("*manifest*.json")]
    sheets = {m["parameters"]["SHEET"] for m in manifests if "parameters" in m}
    assert sheets == {1}, sheets

    # Starting after Stage QC hands off the config's sheet too.
    run_pipeline(workbook, out_root, cfg_dir, start_from="04", runs_dir=out_root / "runs" / "s04", **quiet)
    assert len(pd.read_csv(out_root / FINAL_REL)) == 27


def test_late_resume_ignores_invalid_qc_config(tmp_path: Path) -> None:
    """A resume from 05 or later never loads the QC config.

    Those runs use no QC sheet or handoff, so a QC config the pipeline would
    reject (here, an unmet version requirement) must not abort them. A
    resume from 04 still uses the QC config for the handoff and does reject it.
    """
    import shutil

    out_root = tmp_path / "out"
    quiet = {"log": lambda _: None}
    run_pipeline(EXAMPLE_XLSX, out_root, runs_dir=out_root / "runs" / "full", **quiet)

    cfg_dir = tmp_path / "configs"
    cfg_dir.mkdir()
    shutil.copy(REPO_ROOT / "configs" / "crm_certified_values.yaml", cfg_dir)
    (cfg_dir / "02_ta_ph_qc.yaml").write_text(
        'compatible_pipeline_version: ">=9999.1.0"\nparameters: {}\n', encoding="utf-8"
    )

    for start in ("05", "06", "07", "08"):
        run_pipeline(
            EXAMPLE_XLSX, out_root, cfg_dir, start_from=start, runs_dir=out_root / "runs" / start, **quiet
        )
    assert len(pd.read_csv(out_root / FINAL_REL)) == 27

    with pytest.raises(SystemExit, match="(?i)requires pipeline version"):
        run_pipeline(EXAMPLE_XLSX, out_root, cfg_dir, start_from="04", runs_dir=out_root / "runs" / "s04", **quiet)
