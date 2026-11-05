"""Stage 4's run() through its interface, in process (#42)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from roap import stage4
from roap.stage_config import load_stage_config
from roap.stage_result import MANIFEST_PATH, write_stage_result_to_memory

REPO_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("golden_baseline", REPO_ROOT / "tools" / "golden_baseline.py")
gb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gb)

GOLDEN = gb.GOLDEN_DIR
INPUT = GOLDEN / "oa_stage3_outputs" / "data" / "enhanced.csv"
GOLDEN_OUT = GOLDEN / "oa_stage4_outputs"


def _input() -> pd.DataFrame:
    return pd.read_csv(INPUT)


def _as_canonical(payload: bytes) -> pd.DataFrame:
    return gb.load_canonical(gb.normalize(gb._parse(payload.decode("utf-8"))).to_csv(index=False, lineterminator="\n"))


# The baseline's inputs had their run-specific columns removed, so the column
# inventories (one row per column) are compared by the full pipeline test only.
_COMPARED = sorted(
    str(p.relative_to(GOLDEN_OUT))
    for p in GOLDEN_OUT.rglob("*.csv")
    if p.name not in {"column_inventory.csv", "missingness_top40.csv"}
)


@pytest.mark.parametrize("rel", _COMPARED)
def test_run_matches_golden_stage4_output(rel) -> None:
    files = write_stage_result_to_memory(stage4.run(_input(), load_stage_config("stage4"), source=str(INPUT)))
    expected = gb.load_canonical((GOLDEN_OUT / rel).read_text(encoding="utf-8"))
    assert not gb.compare_frames(_as_canonical(files[rel]), expected)


def test_run_returns_every_stage4_file_and_does_no_disk_io(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = stage4.run(_input(), load_stage_config("stage4"), source="in.csv")
    files = write_stage_result_to_memory(result, parquet=False)

    assert not list(tmp_path.iterdir())
    assert set(files) == {
        "data/analysis_ready.csv",
        *(f"tables/{name}.csv" for name in (
            "column_inventory", "missingness_top40", "canonical_presence", "alias_resolution",
            "missing_key_rows", "duplicates_by_keys", "range_check_summary", "range_flags_long",
            "dic_species_audit",
        )),
        "logs/effective_config.json",
        "reports/report.md",
        MANIFEST_PATH,
    }
    manifest = json.loads(files[MANIFEST_PATH])
    assert manifest["notebook"] == "08_stage4"
    assert manifest["parameters"] == {}
    assert manifest["carbonate_calc"] == {"note": "Skipped (not enabled)."}
    assert manifest["row_counts"]["n_rows"] == len(_input())
    assert files["reports/report.md"].decode().startswith("# Stage 4 Analysis Audit Report")
    assert result.bundle_name == "08_stage4" and result.input_file == "in.csv"


def test_run_leaves_the_input_frame_unchanged() -> None:
    df = _input()
    before = df.copy()
    stage4.run(df, load_stage_config("stage4"))
    pd.testing.assert_frame_equal(df, before)


def test_run_rejects_another_stages_config() -> None:
    with pytest.raises(ValueError, match="stage4 config"):
        stage4.run(_input(), load_stage_config("stage3"))


def test_disabled_audits_are_recorded_and_flag_nothing() -> None:
    result = stage4.run(_input(), load_stage_config("stage4"), range_checks=False, dic_species_check=False)
    assert "Range checks were disabled." in result.manifest["notes"]
    assert "Strict DIC vs species audit disabled." in result.manifest["notes"]
    assert result.tables["tables/range_check_summary.csv"].empty
    assert not result.data["data/analysis_ready.csv"]["flag_dic_species_audit_strict"].any()


def test_carbonate_calc_errors_fail_the_stage(monkeypatch) -> None:
    """An enabled carbonate calculation that fails stops Stage 4 (#44)."""
    from roap import carbonate_calc

    def boom(df, cfg):
        raise RuntimeError("bad inputs")

    monkeypatch.setattr(carbonate_calc, "compute", boom)
    with pytest.raises(SystemExit, match="carbonate calculation failed: RuntimeError: bad inputs") as info:
        stage4.run(_input(), load_stage_config("stage4"), carbonate_calc=True)
    assert isinstance(info.value.__cause__, RuntimeError)
