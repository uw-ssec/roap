# tests/test_golden_baseline.py
"""The pipeline's example-data output matches the golden baseline (#37).

Regenerate with ``pixi run python tools/golden_baseline.py`` and list every
intended difference in the PR description (see tests/golden/README.md).
"""

from __future__ import annotations

import importlib.util
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
    assert gb.normalize(inventory)["example_nonnull"].tolist() == [None, "8.1"]


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
