"""Stage 1B's run() through its interface, in process (#42)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from roap import stage1b
from roap.stage_config import load_stage_config
from roap.stage_result import MANIFEST_PATH, write_stage_result_to_memory

REPO_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("golden_baseline", REPO_ROOT / "tools" / "golden_baseline.py")
gb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gb)

GOLDEN = gb.GOLDEN_DIR
STAGED = GOLDEN / "oa_stage1a_outputs" / "data" / "staged.csv"


def _staged() -> pd.DataFrame:
    return pd.read_csv(STAGED)


def _as_canonical(payload: bytes) -> pd.DataFrame:
    return gb.load_canonical(gb.normalize(gb._parse(payload.decode("utf-8"))).to_csv(index=False, lineterminator="\n"))


def test_run_matches_golden_stage1b_data() -> None:
    files = write_stage_result_to_memory(stage1b.run(_staged(), load_stage_config("stage1b"), source=str(STAGED)))

    for rel in ("data/analysis_fields.csv", "data/analysis_ready_samples.csv"):
        expected = gb.load_canonical((GOLDEN / "oa_stage1b_outputs" / rel).read_text(encoding="utf-8"))
        assert not gb.compare_frames(_as_canonical(files[rel]), expected), rel


def test_run_returns_every_stage1b_file_and_does_no_disk_io(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = stage1b.run(_staged(), load_stage_config("stage1b"), source="staged.csv")
    files = write_stage_result_to_memory(result, parquet=False)

    assert not list(tmp_path.iterdir())
    assert set(files) == {
        "data/analysis_fields.csv",
        "data/analysis_ready_samples.csv",
        "logs/missingness.csv",
        "logs/effective_config.json",
        "reports/report.md",
        MANIFEST_PATH,
    }
    manifest = json.loads(files[MANIFEST_PATH])
    assert manifest["notebook"] == "05_stage1b"
    assert manifest["row_counts"]["analysis_fields_rows"] == len(_staged())
    assert manifest["row_counts"]["analysis_ready_rows"] == len(result.data["data/analysis_ready_samples.csv"])
    assert json.loads(files["logs/effective_config.json"]) == json.loads(json.dumps(result_config(), default=str))
    assert files["reports/report.md"].decode().startswith("# Stage 1B Report")
    assert result.bundle_name == "05_stage1b" and result.input_file == "staged.csv"


def result_config():
    return load_stage_config("stage1b").config


def test_run_leaves_the_input_frame_unchanged() -> None:
    df = _staged()
    before = df.copy()
    stage1b.run(df, load_stage_config("stage1b"))
    pd.testing.assert_frame_equal(df, before)


def test_run_rejects_empty_input_and_wrong_stage_config() -> None:
    with pytest.raises(ValueError, match="empty"):
        stage1b.run(pd.DataFrame(), load_stage_config("stage1b"))
    with pytest.raises(ValueError, match="stage1b config"):
        stage1b.run(_staged(), load_stage_config("stage1a"))
