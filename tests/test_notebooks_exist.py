"""Migration gate: pipeline notebooks are present and are valid notebooks.

The plan listed ``01_preview.ipynb``; no such file exists in the prototype.
The real stage-1 notebook is ``01_excel_viewer.ipynb``, and ``run_pipeline.sh``
invokes it by that name, so the prototype filenames are authoritative here.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_DIR = REPO_ROOT / "notebooks"

# The 8 pipeline-stage notebooks driven by run_pipeline.sh.
NOTEBOOKS = [
    "01_excel_viewer.ipynb",
    "02_ta_ph_qc.ipynb",
    "03_qc_output_review.ipynb",
    "04_stage1a.ipynb",
    "05_stage1b.ipynb",
    "06_stage2.ipynb",
    "07_stage3.ipynb",
    "08_stage4.ipynb",
]


@pytest.mark.parametrize("nb", NOTEBOOKS)
def test_notebook_exists(nb: str) -> None:
    assert (NOTEBOOK_DIR / nb).exists(), f"Missing notebook: {nb}"


@pytest.mark.parametrize("nb", NOTEBOOKS)
def test_notebook_is_valid_json_with_cells(nb: str) -> None:
    """A notebook that does not parse would fail only at Papermill runtime."""
    data = json.loads((NOTEBOOK_DIR / nb).read_text())
    assert "cells" in data, f"{nb} has no cells key"
    assert isinstance(data["cells"], list), f"{nb} cells is not a list"


ALL_NOTEBOOKS = sorted(p.name for p in NOTEBOOK_DIR.glob("*.ipynb")) if NOTEBOOK_DIR.exists() else []


@pytest.mark.parametrize("nb", ALL_NOTEBOOKS)
def test_notebook_has_no_stored_outputs(nb: str) -> None:
    """No notebook ships executed outputs.

    The prototype's oa_figures notebooks embedded real station measurements
    (sample tags, lat/lon, dates, computed TA/pCO2) in their stored outputs.
    Committing those would put unpublished data in git history permanently,
    so outputs are stripped on migration and must stay stripped.
    """
    data = json.loads((NOTEBOOK_DIR / nb).read_text())
    offenders = [
        i
        for i, c in enumerate(data["cells"])
        if c.get("cell_type") == "code" and (c.get("outputs") or c.get("execution_count"))
    ]
    assert not offenders, f"{nb} has stored outputs in cells {offenders}; clear them before committing"


def test_all_runner_notebooks_are_present() -> None:
    """Every notebook run_pipeline.sh references exists in notebooks/.

    Guards the CLI (P1-08) against a missing-notebook failure at run time.
    """
    runner = REPO_ROOT / "run_pipeline.sh"
    if not runner.exists():
        pytest.skip("run_pipeline.sh not yet migrated (P1-08)")

    import re

    referenced = set(re.findall(r"[0-9A-Za-z_]+\.ipynb", runner.read_text()))
    # run.ipynb is the per-run output artifact Papermill writes, not an input.
    referenced.discard("run.ipynb")

    missing = sorted(n for n in referenced if not (NOTEBOOK_DIR / n).exists())
    assert not missing, f"run_pipeline.sh references missing notebooks: {missing}"
