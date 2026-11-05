"""Stage QC's run() through its interface, in process (#42)."""

from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from roap import qc_ta_ph
from roap.common import read_excel_sheets
from roap.stage_config import load_stage_config
from roap.stage_result import MANIFEST_PATH, write_stage_result_to_memory

REPO_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("golden_baseline", REPO_ROOT / "tools" / "golden_baseline.py")
gb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gb)

WORKBOOK = REPO_ROOT / "examples" / "example_data.xlsx"
CRM_VALUES = REPO_ROOT / "configs" / "crm_certified_values.yaml"
GOLDEN_OUT = gb.GOLDEN_DIR / "oa_prelim_data__qc_outputs"


def _qc_config():
    cfg = load_stage_config("qc")
    cfg.load_crm_values(CRM_VALUES)
    return cfg


def _sheets():
    return read_excel_sheets(WORKBOOK, 0)


def _as_canonical(payload: bytes) -> pd.DataFrame:
    return gb.load_canonical(gb.normalize(gb._parse(payload.decode("utf-8"))).to_csv(index=False, lineterminator="\n"))


@pytest.fixture(scope="module")
def files() -> dict:
    return write_stage_result_to_memory(qc_ta_ph.run(_sheets(), _qc_config(), source=str(WORKBOOK)))


@pytest.mark.parametrize("rel", sorted(str(p.relative_to(GOLDEN_OUT)) for p in GOLDEN_OUT.rglob("*.csv")))
def test_run_matches_golden_qc_output(files, rel) -> None:
    expected = gb.load_canonical((GOLDEN_OUT / rel).read_text(encoding="utf-8"))
    assert not gb.compare_frames(_as_canonical(files[rel]), expected)


def test_run_returns_reports_figures_html_and_manifest(files) -> None:
    sheet = "sheet_oa_data"
    assert {
        f"{sheet}/reports/ta_crm_report.md",
        f"{sheet}/reports/phstd_report_tris.md",
        f"{sheet}/figures/rm_ta_diff_qc.jpeg",
        f"{sheet}/figures/phstd_diff_qc_tris.jpeg",
        f"{sheet}/tables/table.html",
        MANIFEST_PATH,
    } <= set(files)
    assert files[f"{sheet}/figures/rm_ta_diff_qc.jpeg"][:2] == b"\xff\xd8"  # JPEG
    assert not any(rel.endswith(".parquet") for rel in files)
    manifest = json.loads(files[MANIFEST_PATH])
    assert manifest["notebook"] == "02_ta_ph_qc"
    assert manifest["config"]["crm_values_path"] == str(CRM_VALUES)
    assert manifest["parameters"]["CRM_VALUES_SOURCE"] == "yaml_file"
    assert manifest["derived_csv_by_sheet"] == {"oa_data": f"{sheet}/data/derived.csv"}


def test_run_without_plots_or_html_and_does_no_disk_io(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = qc_ta_ph.run(_sheets(), _qc_config(), {"WRITE_PLOTS": "no", "WRITE_HTML_TABLE": False})
    assert not result.figures and not result.texts
    write_stage_result_to_memory(result)
    assert not list(tmp_path.iterdir())
    assert result.config_files == [None, str(CRM_VALUES)]


def test_run_leaves_the_input_sheets_unchanged() -> None:
    sheets = _sheets()
    before = {name: df.copy() for name, df in sheets.items()}
    qc_ta_ph.run(sheets, _qc_config())
    for name, df in sheets.items():
        pd.testing.assert_frame_equal(df, before[name])


@pytest.mark.parametrize(
    "params, match",
    [
        ({"MIN_CRM_N": 0}, "MIN_CRM_N"),
        ({"TA_REJECT": 1.0}, "TA_REJECT"),
        ({"PH_WARN": 0.01}, "PH_WARN"),
        ({"PH_BUFFER": "acid"}, "PH_BUFFER"),
        ({"ROW_ROLE_PREFIXES": {"NOPE": "X"}}, "ROW_ROLE_PREFIXES"),
        ({"WRITE_DERIVED_CSV": False}, "WRITE_DERIVED_CSV"),
    ],
)
def test_unusable_parameters_are_rejected(params, match) -> None:
    with pytest.raises(ValueError, match=match):
        qc_ta_ph.qc_run_parameters(params)


def test_run_rejects_another_stages_config() -> None:
    with pytest.raises(ValueError, match="qc config"):
        qc_ta_ph.run(_sheets(), load_stage_config("stage1a"))


def test_run_defaults_match_notebook_02_parameters_cell() -> None:
    nb = json.loads((REPO_ROOT / "notebooks" / "02_ta_ph_qc.ipynb").read_text(encoding="utf-8"))
    cell = next(c for c in nb["cells"] if "parameters" in c.get("metadata", {}).get("tags", []))
    values = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in ast.parse("".join(cell["source"])).body
        if isinstance(node, ast.Assign) and node.targets[0].id in qc_ta_ph.QC_RUN_DEFAULTS
    }
    assert values == qc_ta_ph.QC_RUN_DEFAULTS
