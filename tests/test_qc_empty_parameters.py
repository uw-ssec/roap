# tests/test_qc_empty_parameters.py
"""Notebook 02 runs on its defaults when the config's ``parameters:`` is empty (#41).

An empty YAML block loads as None. roap.stage_config must hand the notebook
an empty mapping, not None, or ``config["parameters"].items()`` crashes.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("papermill")

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.slow
def test_qc_notebook_accepts_an_empty_parameters_block(tmp_path: Path) -> None:
    config = tmp_path / "02_ta_ph_qc.yaml"
    config.write_text('compatible_pipeline_version: ">=0.2.0"\nparameters:\n', encoding="utf-8")
    out_dir = tmp_path / "qc_outputs"

    env = {k: v for k, v in os.environ.items() if k != "GIT_COMMIT"}
    result = subprocess.run(
        [
            sys.executable, "-m", "papermill", "02_ta_ph_qc.ipynb", str(tmp_path / "02.run.ipynb"),
            "-p", "OUT_DIR", str(out_dir),
            "-p", "CONFIG_PATH", str(config),
        ],
        cwd=REPO_ROOT / "notebooks", capture_output=True, text=True, env=env, timeout=300,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert any(out_dir.rglob("derived.csv"))
