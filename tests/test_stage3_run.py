"""Stage 3's run() through its interface, in process (#42)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from roap import stage3
from roap.stage_config import load_stage_config
from roap.stage_result import MANIFEST_PATH, write_stage_result_to_memory

REPO_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("golden_baseline", REPO_ROOT / "tools" / "golden_baseline.py")
gb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gb)

GOLDEN = gb.GOLDEN_DIR
INPUT = GOLDEN / "oa_stage2_outputs" / "data" / "enhanced.csv"
GOLDEN_OUT = GOLDEN / "oa_stage3_outputs"


def _input() -> pd.DataFrame:
    return pd.read_csv(INPUT)


def _as_canonical(payload: bytes) -> pd.DataFrame:
    return gb.load_canonical(gb.normalize(gb._parse(payload.decode("utf-8"))).to_csv(index=False, lineterminator="\n"))


# The baseline's inputs had their run-specific columns removed, so the column
# inventory (one row per column) is compared by the full pipeline test only.
_COMPARED = sorted(
    str(p.relative_to(GOLDEN_OUT)) for p in GOLDEN_OUT.rglob("*.csv") if p.name != "column_inventory.csv"
)


@pytest.mark.parametrize("rel", _COMPARED)
def test_run_matches_golden_stage3_output(rel) -> None:
    files = write_stage_result_to_memory(stage3.run(_input(), load_stage_config("stage3"), source=str(INPUT)))
    expected = gb.load_canonical((GOLDEN_OUT / rel).read_text(encoding="utf-8"))
    assert not gb.compare_frames(_as_canonical(files[rel]), expected)


def test_run_returns_every_stage3_file_and_does_no_disk_io(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = stage3.run(_input(), load_stage_config("stage3"), source="in.csv", depth_round_decimals=2)
    files = write_stage_result_to_memory(result, parquet=False)

    assert not list(tmp_path.iterdir())
    assert set(files) == {
        "data/enhanced.csv",
        *(f"tables/{name}.csv" for name in (
            "carbonate_integrity_flags", "qc_summary_by_group", "dic_species_mismatches",
            "ph_diag_mismatches", "column_inventory", "canonical_presence", "alias_resolution",
        )),
        "logs/effective_config.json",
        "reports/report.md",
        MANIFEST_PATH,
    }
    manifest = json.loads(files[MANIFEST_PATH])
    assert manifest["notebook"] == "07_stage3"
    assert manifest["parameters"] == {"DEPTH_ROUND_DECIMALS": 2}
    assert manifest["row_counts"]["n_rows"] == len(_input())
    assert files["reports/report.md"].decode().startswith("# Stage 3 Preprocessing Report")
    assert result.bundle_name == "07_stage3" and result.input_file == "in.csv"


def test_run_leaves_the_input_frame_unchanged() -> None:
    df = _input()
    before = df.copy()
    stage3.run(df, load_stage_config("stage3"))
    pd.testing.assert_frame_equal(df, before)


def test_run_rejects_bad_arguments() -> None:
    with pytest.raises(ValueError, match="stage3 config"):
        stage3.run(_input(), load_stage_config("stage2"))
    with pytest.raises(ValueError, match=">= 0"):
        stage3.run(_input(), load_stage_config("stage3"), depth_round_decimals=-1)
