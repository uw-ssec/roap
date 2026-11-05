"""Stage 1A's run() through its interface, in process (#42)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from roap import stage1a
from roap.stage_config import load_stage_config
from roap.stage_result import MANIFEST_PATH, write_stage_result_to_memory

REPO_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("golden_baseline", REPO_ROOT / "tools" / "golden_baseline.py")
gb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gb)

GOLDEN = gb.GOLDEN_DIR
QC_DERIVED = next(GOLDEN.glob("oa_prelim_data__qc_outputs/*/data/derived.csv"))


def _derived() -> pd.DataFrame:
    return pd.read_csv(QC_DERIVED)


def _golden_frame(rel: str) -> pd.DataFrame:
    return gb.load_canonical((GOLDEN / "oa_stage1a_outputs" / rel).read_text(encoding="utf-8"))


def _as_canonical(payload: bytes) -> pd.DataFrame:
    return gb.load_canonical(gb.normalize(gb._parse(payload.decode("utf-8"))).to_csv(index=False, lineterminator="\n"))


def test_run_matches_golden_stage1a_data() -> None:
    result = stage1a.run(_derived(), load_stage_config("stage1a"), source=str(QC_DERIVED))
    files = write_stage_result_to_memory(result)

    for rel in ("data/staged.csv", "data/analysis_ready.csv"):
        assert not gb.compare_frames(_as_canonical(files[rel]), _golden_frame(rel)), rel
    assert {"data/staged.parquet", "data/analysis_ready.parquet"} <= set(files)


def test_run_returns_every_stage1a_file_and_does_no_disk_io(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = stage1a.run(_derived(), load_stage_config("stage1a"), source="derived.csv")
    files = write_stage_result_to_memory(result, parquet=False)

    assert not list(tmp_path.iterdir())
    assert set(files) == {
        "data/staged.csv",
        "data/analysis_ready.csv",
        "logs/rename_audit.csv",
        "logs/canonical_inventory.csv",
        "logs/missingness.csv",
        "logs/effective_config.json",
        "logs/source_lookup.json",
        "reports/report.md",
        MANIFEST_PATH,
    }
    manifest = json.loads(files[MANIFEST_PATH])
    assert manifest["notebook"] == "04_stage1a"
    assert manifest["row_counts"]["staged_rows"] == len(_derived())
    assert manifest["parquet"]["data/staged.csv"] == {"written": False, "error": "Parquet disabled by user"}
    assert files["reports/report.md"].decode().startswith("# Stage 1A Report")
    assert result.bundle_name == "04_stage1a" and result.input_file == "derived.csv"


def test_run_leaves_the_input_frame_unchanged() -> None:
    df = _derived()
    before = df.copy()
    stage1a.run(df, load_stage_config("stage1a"))
    pd.testing.assert_frame_equal(df, before)


def test_duplicate_key_override_is_used_and_checked() -> None:
    df = pd.DataFrame({"sample_id": ["A", "A", "B"], "ta": [2200, 2200, 2100]})
    result = stage1a.run(df, load_stage_config("stage1a"), duplicate_keys=["sample_id"])
    assert result.manifest["policy"]["duplicate_keys_used"] == ["sample_id"]
    assert result.manifest["row_counts"]["possible_duplicate_rows"] == 2

    with pytest.raises(ValueError, match="not present"):
        stage1a.run(df, load_stage_config("stage1a"), duplicate_keys=["nope"])


def test_run_rejects_empty_input_and_wrong_stage_config() -> None:
    with pytest.raises(ValueError, match="empty"):
        stage1a.run(pd.DataFrame(), load_stage_config("stage1a"))
    with pytest.raises(ValueError, match="stage1a config"):
        stage1a.run(_derived(), load_stage_config("stage2"))
