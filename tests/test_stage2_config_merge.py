# tests/test_stage2_config_merge.py
"""Notebook 06 (Stage 2) keeps user config keys (#39).

The merge used to keep only keys already in STAGE2_DEFAULTS, so any other
user key (for example ``required_stage2_input_columns``, which the notebook
reads) was silently dropped. roap.stage_config (#41) later replaces the
per-notebook merges.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

pytest.importorskip("papermill")

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.slow
def test_stage2_user_config_key_reaches_effective_config(tmp_path: Path) -> None:
    input_csv = tmp_path / "analysis_ready_samples.csv"
    input_csv.write_text(
        "sample_id,sample_date,station_id,depth_m,ta_best_umolkg,ph_best\n"
        "S001,2024-01-01,ST1,5.0,2200,8.0\n",
        encoding="utf-8",
    )
    config = tmp_path / "06_stage2.yaml"
    # Not a STAGE2_DEFAULTS key, but one the notebook reads.
    user_key = {"required_stage2_input_columns": ["sample_id", "station_id"]}
    # A STAGE2_DEFAULTS key, which the old merge kept too.
    default_key = {"depth_bin_m": 2.5}
    config.write_text(yaml.safe_dump({**user_key, **default_key}), encoding="utf-8")
    out_dir = tmp_path / "oa_stage2_outputs"

    env = {k: v for k, v in os.environ.items() if k != "GIT_COMMIT"}
    result = subprocess.run(
        [
            sys.executable, "-m", "papermill", "06_stage2.ipynb", str(tmp_path / "06.run.ipynb"),
            "-p", "INPUT_CSV", str(input_csv),
            "-p", "OUT_DIR", str(out_dir),
            "-p", "CONFIG_PATH", str(config),
            "-p", "NO_PARQUET", "True",
        ],
        cwd=REPO_ROOT / "notebooks", capture_output=True, text=True, env=env, timeout=300,
    )
    assert result.returncode == 0, result.stderr[-2000:]

    effective = json.loads((out_dir / "logs" / "effective_config.json").read_text(encoding="utf-8"))
    assert effective["required_stage2_input_columns"] == ["sample_id", "station_id"]
    assert effective["depth_bin_m"] == 2.5
