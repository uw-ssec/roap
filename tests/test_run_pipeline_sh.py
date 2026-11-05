"""run_pipeline.sh end to end: the shell wrapper the GUI calls (#43).

The engine itself is tested in process (test_pipeline_e2e.py). This smoke
test covers what only the wrapper does: argument parsing, path handling,
passing --config-dir and --no-parquet through to ``roap run``, and the run
bundle written into the runs directory the wrapper picks.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from roap.bundle import check_bundle

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_XLSX = REPO_ROOT / "examples" / "example_data.xlsx"


@pytest.mark.slow
def test_run_pipeline_sh_runs_end_to_end(tmp_path: Path, bash_exe: str) -> None:
    # configs/ targets another workbook; its Stage QC file names columns the
    # example data lacks, so keep only the downstream Stage configs.
    config_dir = tmp_path / "configs"
    shutil.copytree(REPO_ROOT / "configs", config_dir)
    (config_dir / "02_ta_ph_qc.yaml").unlink()
    out_root = tmp_path / "out"

    result = subprocess.run(
        [
            bash_exe,
            "./run_pipeline.sh",
            EXAMPLE_XLSX.relative_to(REPO_ROOT).as_posix(),
            out_root.as_posix(),
            "--config-dir",
            config_dir.as_posix(),
            "--no-parquet",
        ],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHON_BIN": sys.executable},
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert result.returncode == 0, f"run_pipeline.sh failed:\n{result.stdout[-4000:]}\n{result.stderr[-4000:]}"
    assert "Pipeline complete." in result.stdout

    assert (out_root / "oa_stage4_outputs" / "data" / "analysis_ready.csv").is_file()
    assert not list(out_root.rglob("*.parquet")), "--no-parquet was not passed through"
    assert not list(out_root.rglob("*.ipynb")), "Stages should run in process, not through papermill"

    stage4 = (out_root / "oa_stage4_outputs" / "logs" / "manifest.json").read_text(encoding="utf-8")
    assert "08_stage4.yaml" in stage4, "--config-dir was not passed through"

    match = re.search(r"--runs-dir (\S+)", result.stdout)
    assert match, result.stdout
    run_dir = Path(match.group(1))
    try:
        report = check_bundle(run_dir)
        assert report["valid"], report
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
