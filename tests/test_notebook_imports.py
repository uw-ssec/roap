"""Guard: notebooks must not reference the pre-rename package name in code.

Background — this is a regression test for a real, silent failure.

``notebooks/08_stage4.ipynb`` carried ``from oa_pipeline import carbonate_calc``
inside a ``try/except Exception`` that recorded the error and continued. After
the oa_pipeline->roap rename the import raised ``ModuleNotFoundError``, so
enabling carbonate chemistry produced an ``analysis_ready.csv`` with **no
computed chemistry at all** while ``run_pipeline.sh`` still exited 0 and printed
"Pipeline complete."

For a reproducibility tool a silent wrong answer is worse than a crash, so:

* no executable notebook cell may reference ``oa_pipeline`` / ``oa-pipeline``;
* the carbonate_calc import must sit OUTSIDE the try/except that guards the
  computation, so a broken install fails loudly.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = sorted((REPO_ROOT / "notebooks").glob("*.ipynb"))

# The figure notebooks carry stale Windows INPUT paths containing the old
# project directory name. Those are interactive defaults overridden on every
# run, not imports, so they are tracked separately rather than silently allowed.
_WINDOWS_PATH_MARKER = r"C:\Users"


def _code_lines(nb_path: Path):
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        for line in cell.get("source", []):
            yield idx, line


@pytest.mark.parametrize("nb_path", NOTEBOOKS, ids=lambda p: p.name)
def test_no_old_package_name_in_code_cells(nb_path: Path) -> None:
    """No executable cell imports or version-queries the old package name."""
    offenders = []
    for idx, line in _code_lines(nb_path):
        if _WINDOWS_PATH_MARKER in line:
            continue  # stale interactive default, not an import
        if "oa_pipeline" in line or "oa-pipeline" in line:
            offenders.append(f"cell{idx}: {line.strip()}")

    assert not offenders, (
        f"{nb_path.name} still references the pre-rename package in executable "
        f"code:\n  " + "\n  ".join(offenders)
    )


def test_stage4_carbonate_import_is_not_swallowed() -> None:
    """The carbonate_calc import must not sit inside the try/except.

    If it does, a broken install silently yields no chemistry while the
    pipeline reports success.
    """
    nb = json.loads((REPO_ROOT / "notebooks" / "08_stage4.ipynb").read_text(encoding="utf-8"))

    cell_src = None
    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        if "carbonate_calc" in src and "import" in src:
            cell_src = src
            break

    assert cell_src is not None, "Could not find the carbonate_calc cell"
    assert "from roap import carbonate_calc" in cell_src, (
        "08_stage4 must import carbonate_calc from roap"
    )

    lines = cell_src.splitlines()
    import_idx = next(
        i for i, ln in enumerate(lines) if "from roap import carbonate_calc" in ln
    )
    try_idx = next(
        (i for i, ln in enumerate(lines) if ln.strip() == "try:" and i > import_idx),
        None,
    )
    assert try_idx is not None and try_idx > import_idx, (
        "The carbonate_calc import must appear BEFORE the try/except guarding "
        "the computation, so an unimportable engine fails loudly instead of "
        "silently producing an analysis_ready.csv with no chemistry."
    )
