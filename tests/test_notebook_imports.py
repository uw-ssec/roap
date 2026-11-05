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
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = sorted((REPO_ROOT / "notebooks").glob("*.ipynb"))

_USER_PATH = re.compile(r"[A-Za-z]:[\\/]Users[\\/]|/(?:Users|home)/", re.IGNORECASE)


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
        if "oa_pipeline" in line or "oa-pipeline" in line:
            offenders.append(f"cell{idx}: {line.strip()}")

    assert not offenders, (
        f"{nb_path.name} still references the pre-rename package in executable "
        f"code:\n  " + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("nb_path", NOTEBOOKS, ids=lambda p: p.name)
def test_no_absolute_user_paths_in_code_cells(nb_path: Path) -> None:
    """Interactive defaults must work outside a contributor's home directory."""
    offenders = [
        f"cell{idx}: {line.strip()}"
        for idx, line in _code_lines(nb_path)
        if _USER_PATH.search(line)
    ]
    assert not offenders, (
        f"{nb_path.name} contains absolute user paths in executable code:\n  "
        + "\n  ".join(offenders)
    )


def test_stage4_carbonate_import_is_not_swallowed(monkeypatch) -> None:
    """An unimportable carbonate_calc fails Stage 4 instead of being swallowed.

    Stage 4's run() (#42) records carbonate *computation* errors and carries
    on; if it also swallowed the import, a broken install would silently
    yield no chemistry while the pipeline reports success.
    """
    import sys

    import pandas as pd

    import roap
    from roap import stage4
    from roap.stage_config import load_stage_config

    monkeypatch.setitem(sys.modules, "roap.carbonate_calc", None)
    monkeypatch.delattr(roap, "carbonate_calc", raising=False)
    frame = pd.read_csv(REPO_ROOT / "tests" / "golden" / "example_data" / "oa_stage3_outputs" / "data" / "enhanced.csv")

    with pytest.raises(ImportError):
        stage4.run(frame, load_stage_config("stage4"), carbonate_calc=True)

    nb = json.loads((REPO_ROOT / "notebooks" / "08_stage4.ipynb").read_text(encoding="utf-8"))
    code = "".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    assert "carbonate_calc=not NO_CARBONATE_CALC" in code
    # The cell around stage4.run catches only ValueError, so an ImportError
    # from run() stops the notebook.
    run_block = code[code.rindex("try:", 0, code.index("stage4.run(")) : code.index("die(str(exc))")]
    assert "except ValueError as exc:" in run_block and "except Exception" not in run_block
