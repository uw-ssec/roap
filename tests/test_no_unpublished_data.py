"""Guard: no unpublished research data is tracked in git.

The only data file this repo may track is the synthetic example workbook.
Everything else -- real cruise workbooks, pipeline outputs, run bundles --
stays out of git history, where it could not be removed without a rewrite.
"""

import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

ALLOWED_DATA_FILES = {"examples/example_data.xlsx"}

DATA_SUFFIXES = {".xlsx", ".xls", ".csv", ".parquet", ".nc", ".dat"}

# Directories the pipeline writes into; none may ever be tracked.
OUTPUT_DIRS = ["runs", "outputs"]


def _tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, cwd=REPO_ROOT, timeout=120
    )
    assert out.returncode == 0, out.stderr
    return [line for line in out.stdout.splitlines() if line]


def test_no_unexpected_data_files_tracked() -> None:
    tracked = _tracked_files()
    data_files = {f for f in tracked if Path(f).suffix.lower() in DATA_SUFFIXES}
    # The prototype submodule is a separate repo; its contents are not ours.
    data_files = {f for f in data_files if not f.startswith("references/")}

    unexpected = sorted(data_files - ALLOWED_DATA_FILES)
    assert not unexpected, f"Unpublished data files tracked in git: {unexpected}"


def test_example_workbook_is_synthetic() -> None:
    """The one allowed workbook must be generator output, not real measurements."""
    pd = pytest.importorskip("pandas")
    df = pd.read_excel(REPO_ROOT / "examples" / "example_data.xlsx")

    assert set(df["carbonate_solver"].dropna().unique()) == {"synthetic_example_generator"}
    assert df["sample_tag"].str.match(r"^(S\d+|RM\d+|TRIS)").all(), (
        "example workbook contains tags that do not look generator-made"
    )


@pytest.mark.parametrize("dirname", OUTPUT_DIRS)
def test_pipeline_output_dirs_are_not_tracked(dirname: str) -> None:
    tracked = [f for f in _tracked_files() if f.startswith(f"{dirname}/")]
    assert not tracked, f"{dirname}/ holds pipeline output and must not be tracked: {tracked[:10]}"


@pytest.mark.parametrize("dirname", OUTPUT_DIRS)
def test_pipeline_output_dirs_are_gitignored(dirname: str) -> None:
    """Ignored, so a stray `git add -A` after a run cannot commit real data."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", f"{dirname}/"],
        cwd=REPO_ROOT,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"{dirname}/ is not gitignored; a pipeline run followed by `git add -A` "
        f"would commit its output"
    )


def test_notebooks_carry_no_stored_outputs() -> None:
    """Executed outputs can embed real measurements (see P1-07)."""
    offenders = []
    for nb_path in sorted((REPO_ROOT / "notebooks").glob("*.ipynb")):
        nb = json.loads(nb_path.read_text())
        for i, cell in enumerate(nb["cells"]):
            if cell.get("cell_type") == "code" and (
                cell.get("outputs") or cell.get("execution_count")
            ):
                offenders.append(f"{nb_path.name}:cell{i}")
    assert not offenders, f"Notebooks with stored outputs: {offenders}"
