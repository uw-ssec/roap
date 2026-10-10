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

# Executed notebooks and exported reports embed measurement tables inline, so
# they count as data when they appear under an output directory.
OUTPUT_DATA_SUFFIXES = DATA_SUFFIXES | {".ipynb", ".html"}

# Directories the pipeline writes into; none may ever be tracked.
OUTPUT_DIRS = ["runs", "outputs", ".pytest_runs"]

# Markers for the unpublished April 2026 cruise. Any of these appearing in a
# tracked file means real measurements leaked.
UNPUBLISHED_MARKERS = ["P4506", "2026-04-15", "P4504-S1", "oa_prelim_data.xlsx:"]


def _tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, cwd=REPO_ROOT, timeout=120
    )
    assert out.returncode == 0, out.stderr
    return [line for line in out.stdout.splitlines() if line]


def test_no_unexpected_data_files_tracked() -> None:
    tracked = _tracked_files()
    data_files = {f for f in tracked if Path(f).suffix.lower() in DATA_SUFFIXES}
    # The prototype submodule is a separate repo with its own history; its
    # contents are covered by test_prototype_submodule_has_no_stored_outputs.
    data_files = {f for f in data_files if not f.startswith("references/")}

    unexpected = sorted(data_files - ALLOWED_DATA_FILES)
    assert not unexpected, f"Unpublished data files tracked in git: {unexpected}"


def test_prototype_submodule_has_no_stored_outputs() -> None:
    """The pinned submodule commit must not carry executed notebook outputs.

    A submodule gitlink is a durable pointer: `git clone --recursive` fetches
    whatever commit is pinned here. Stripping outputs from our *copy* of the
    figure notebooks (P1-07) does nothing about the original, so this asserts
    the pinned commit itself is clean.
    """
    sub = REPO_ROOT / "references" / "prototype" / "oa_pipeline"
    if not (sub / ".git").exists():
        pytest.skip("prototype submodule not checked out")

    offenders = []
    for nb_path in sorted(sub.glob("notebooks/*.ipynb")):
        try:
            nb = json.loads(nb_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for i, cell in enumerate(nb.get("cells", [])):
            if cell.get("cell_type") == "code" and cell.get("outputs"):
                offenders.append(f"{nb_path.name}:cell{i}")

    assert not offenders, (
        "The pinned prototype submodule commit carries executed notebook "
        f"outputs, which embed real measurements: {offenders[:10]}. "
        "Strip them upstream and re-pin the submodule."
    )


def test_no_unpublished_cruise_markers_in_tracked_files() -> None:
    """No tracked file in this repo contains April 2026 cruise identifiers."""
    # Prose that names the dataset is fine; measurements are not. These files
    # discuss the cruise by name as documentation.
    allowed = {
        "tests/test_no_unpublished_data.py",  # defines the markers
        "knowledge/prototype/requested-dataset.md",  # documents it as withheld
    }

    offenders = []
    for rel in _tracked_files():
        if rel.startswith("references/") or rel in allowed:
            continue  # separate repo; covered by the submodule test above
        path = REPO_ROOT / rel
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        try:
            text = path.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        for marker in UNPUBLISHED_MARKERS:
            if marker in text:
                offenders.append(f"{rel} contains {marker!r}")

    assert not offenders, f"Unpublished cruise data in tracked files: {offenders[:10]}"


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
