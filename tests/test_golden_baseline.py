# tests/test_golden_baseline.py
"""The pipeline's example-data output matches the golden baseline (#37).

Regenerate with ``pixi run python tools/golden_baseline.py`` and list every
intended difference in the PR description (see tests/golden/README.md).
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("papermill")

REPO_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "golden_baseline", REPO_ROOT / "tools" / "golden_baseline.py"
)
gb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gb)


@pytest.fixture(scope="module")
def pipeline_out(tmp_path_factory: pytest.TempPathFactory, bash_exe: str) -> Path:
    out_root = tmp_path_factory.mktemp("golden") / "out"
    gb.run_pipeline(out_root, bash=bash_exe)
    return out_root


@pytest.mark.slow
def test_example_output_matches_golden_baseline(pipeline_out: Path) -> None:
    problems = gb.compare(pipeline_out)
    assert not problems, (
        "Pipeline output differs from tests/golden/example_data. If the change is "
        "intended, run `pixi run python tools/golden_baseline.py` and list each "
        "difference in the PR description.\n" + "\n".join(problems)
    )


def test_golden_baseline_covers_every_stage() -> None:
    stages = {p.parts[0] for p in gb.output_csvs(gb.GOLDEN_DIR)}
    assert stages == {
        "oa_prelim_data__qc_outputs",
        "oa_stage1a_outputs",
        "oa_stage1b_outputs",
        "oa_stage2_outputs",
        "oa_stage3_outputs",
        "oa_stage4_outputs",
    }


def test_normalize_drops_run_specific_columns() -> None:
    df = pd.DataFrame(
        {
            "sample_id": ["S1"],
            "source_file": ["/tmp/x.csv"],
            "source_file_stage2": ["/tmp/y.csv"],
            "stage2_processed_utc": ["2026-11-05T00:00:00Z"],
            "ta_best_umolkg": [2300.0],
        }
    )
    assert gb.normalize(df).columns.tolist() == ["sample_id", "ta_best_umolkg"]

    inventory = pd.DataFrame(
        {"column": ["source_file", "ph_best"], "example_nonnull": ["/tmp/x.csv", "8.1"]}
    )
    assert gb.normalize(inventory)["example_nonnull"].tolist() == ["", "8.1"]


def test_compare_reports_value_and_file_differences(tmp_path: Path) -> None:
    golden, fresh = tmp_path / "golden", tmp_path / "fresh"
    for root, value in ((golden, "2300.0"), (fresh, "2300.5")):
        (root / "oa_stage4_outputs" / "data").mkdir(parents=True)
        (root / "oa_stage4_outputs" / "data" / "analysis_ready.csv").write_text(
            f"sample_id,ta_best_umolkg\nS1,{value}\n", encoding="utf-8"
        )
    (fresh / "oa_stage4_outputs" / "data" / "extra.csv").write_text("a\n1\n", encoding="utf-8")

    problems = gb.compare(fresh, golden)
    assert any(p.startswith("oa_stage4_outputs/data/analysis_ready.csv:") for p in problems)
    assert "new output not in baseline: oa_stage4_outputs/data/extra.csv" in problems
    # A difference within tolerance is not reported.
    (fresh / "oa_stage4_outputs" / "data" / "analysis_ready.csv").write_text(
        "sample_id,ta_best_umolkg\nS1,2300.0000000000005\n", encoding="utf-8"
    )
    (fresh / "oa_stage4_outputs" / "data" / "extra.csv").unlink()
    assert gb.compare(fresh, golden) == []


def _fixture_pair(tmp_path: Path, golden_text: str, fresh_text: str) -> list[str]:
    golden, fresh = tmp_path / "golden", tmp_path / "fresh"
    for root, text in ((golden, golden_text), (fresh, fresh_text)):
        (root / "oa_stage1b_outputs" / "data").mkdir(parents=True)
        (root / "oa_stage1b_outputs" / "data" / "ta_crm_qc.csv").write_text(text, encoding="utf-8")
    return gb.compare(fresh, golden)


@pytest.mark.parametrize(
    ("golden_text", "fresh_text"),
    [
        # An identifier that type inference would read as the same integer.
        ("sample_id,crm_batch\nRM1,213\n", "sample_id,crm_batch\nRM1,0213\n"),
        # A literal NA that default NA parsing would read as an empty cell.
        ("sample_id,station_id\nS1,\n", "sample_id,station_id\nS1,NA\n"),
        # An integer count is exact even when the difference is within tolerance.
        ("group,n\nA,1000000000000\n", "group,n\nA,1000000000001\n"),
        # Identifiers that look like floats are still exact text.
        ("sample_id,station_id\nS1,1.0\n", "sample_id,station_id\nS1,01.0\n"),
        ("sample_id,station_id\n1e12,V01\n", "sample_id,station_id\n1.000000000001e12,V01\n"),
        # A float-formatted count is exact too: counts are not in FLOAT_COLUMNS.
        ("group,n_rows\nA,7.0\n", "group,n_rows\nA,7.000000000001\n"),
    ],
    ids=[
        "leading-zero-identifier",
        "empty-vs-literal-NA",
        "integer-count",
        "float-like-station-id",
        "float-like-sample-id",
        "float-formatted-count",
    ],
)
def test_compare_reports_text_changes_inference_would_hide(
    tmp_path: Path, golden_text: str, fresh_text: str
) -> None:
    problems = _fixture_pair(tmp_path, golden_text, fresh_text)
    assert len(problems) == 1 and problems[0].startswith("oa_stage1b_outputs/data/ta_crm_qc.csv:")


def test_compare_applies_tolerance_only_between_floats(tmp_path: Path) -> None:
    golden = "ph_best\n0.013999999999999346\n"
    assert _fixture_pair(tmp_path / "a", golden, "ph_best\n0.0139999999999993\n") == []
    assert _fixture_pair(tmp_path / "b", golden, "ph_best\n0.0141\n") != []
    assert _fixture_pair(tmp_path / "c", golden, "ph_best\nabc\n") != []
    # The same last-digit difference outside FLOAT_COLUMNS is reported.
    golden = "x\n0.013999999999999346\n"
    assert _fixture_pair(tmp_path / "d", golden, "x\n0.0139999999999993\n") != []


def _baseline_columns() -> set[str]:
    return {
        str(c) for p in gb.output_csvs(gb.GOLDEN_DIR) for c in gb._read(gb.GOLDEN_DIR / p).columns
    }


def test_float_columns_are_current_and_exclude_identifiers() -> None:
    assert not gb.FLOAT_COLUMNS - _baseline_columns(), "FLOAT_COLUMNS names a column no stage writes"
    identifier = re.compile(r"(_id|batch|flag|station|sample|cast|bottle|niskin)", re.IGNORECASE)
    assert not {c for c in gb.FLOAT_COLUMNS if identifier.search(c)}
    assert not {c for c in gb.FLOAT_COLUMNS if c == "n" or c.startswith("n_")}
