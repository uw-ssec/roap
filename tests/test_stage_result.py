# tests/test_stage_result.py
"""StageResult and its disk and in-memory writers (#42, ADR-0011)."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd
import pytest

from roap.bundle import check_bundle
from roap.stage_result import (
    MANIFEST_PATH,
    StageResult,
    package_versions,
    write_stage_result,
    write_stage_result_to_memory,
)


def _result(tmp_path: Path) -> StageResult:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot([1, 2], [3, 4])
    src = tmp_path / "input.csv"
    src.write_text("a\n1\n", encoding="utf-8")
    return StageResult(
        stage="demo",
        data={"data/out.csv": pd.DataFrame({"a": [1.0, None], "t": pd.to_datetime(["2026-01-02", None], utc=True)})},
        tables={"logs/missingness.csv": pd.DataFrame({"column": ["a"], "n": [1]})},
        reports={"reports/report.md": "# Report\n"},
        figures={"figures/plot.jpeg": fig},
        texts={"logs/effective_config.json": json.dumps({"k": 1})},
        manifest={"notebook": "demo", "rows": 2},
        input_file=str(src),
        bundle_name="demo",
    )


def test_memory_writer_renders_every_file_and_the_manifest(tmp_path) -> None:
    files = write_stage_result_to_memory(_result(tmp_path))
    assert set(files) == {
        "data/out.csv", "data/out.parquet", "logs/missingness.csv", "reports/report.md",
        "figures/plot.jpeg", "logs/effective_config.json", MANIFEST_PATH,
    }
    # Data CSVs use write_csv_and_parquet's stable settings.
    assert files["data/out.csv"].decode() == "a,t\n1.0,2026-01-02T00:00:00Z\n,\n"
    assert pd.read_parquet(io.BytesIO(files["data/out.parquet"]))["a"].iloc[0] == 1.0
    assert files["figures/plot.jpeg"][:2] == b"\xff\xd8"
    manifest = json.loads(files[MANIFEST_PATH])
    assert manifest["rows"] == 2
    assert manifest["parquet"] == {"data/out.csv": {"written": True, "error": None}}
    assert "data/out.parquet" in manifest["outputs"]


def test_memory_writer_without_parquet(tmp_path) -> None:
    files = write_stage_result_to_memory(_result(tmp_path), parquet=False)
    assert "data/out.parquet" not in files
    assert json.loads(files[MANIFEST_PATH])["parquet"]["data/out.csv"]["written"] is False


def test_disk_writer_matches_memory_writer_and_writes_a_valid_bundle(tmp_path) -> None:
    result = _result(tmp_path)
    out = tmp_path / "out"
    written = write_stage_result(result, out)
    memory = write_stage_result_to_memory(result)
    for rel, payload in memory.items():
        if rel in (MANIFEST_PATH, "figures/plot.jpeg"):
            continue
        assert (out / rel).read_bytes() == payload, rel
    assert set(written) == set(memory)
    manifest = json.loads((out / MANIFEST_PATH).read_text(encoding="utf-8"))
    assert str(out.resolve() / "data" / "out.csv") in manifest["outputs"]
    assert not list(out.rglob("*.tmp"))
    report = check_bundle(out)
    assert report["valid"], report
    bundled = {Path(c["path"]).name for c in report["checks"] if c["kind"] == "output"}
    assert {"out.csv", "out.parquet", "plot.jpeg", "manifest.json"} <= bundled
    configs = {Path(c["path"]).name for c in report["checks"] if c["kind"] == "config"}
    assert configs == {"effective_config.json"}


def test_disk_writer_needs_bundle_provenance(tmp_path) -> None:
    result = _result(tmp_path)
    result.input_file = None
    with pytest.raises(ValueError, match="input_file"):
        write_stage_result(result, tmp_path / "out")
    write_stage_result(result, tmp_path / "out2", bundle=False)


@pytest.mark.parametrize("rel", ["/abs.csv", "../up.csv", "noext", MANIFEST_PATH])
def test_bad_paths_are_rejected(tmp_path, rel) -> None:
    result = StageResult(stage="demo", texts={rel: "x"})
    with pytest.raises(ValueError):
        write_stage_result_to_memory(result)


def test_package_versions_names_the_core_packages() -> None:
    versions = package_versions()
    assert versions["pandas"] == pd.__version__
    assert {"python", "numpy", "matplotlib", "roap"} <= set(versions)
