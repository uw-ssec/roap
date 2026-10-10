"""Migration gate: example dataset is present and regeneratable."""

import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"
EXAMPLE_XLSX = EXAMPLES_DIR / "example_data.xlsx"

EXPECTED_ROWS = 27  # 20 samples + 4 CRM + 3 TRIS
EXPECTED_CRM = 4
EXPECTED_TRIS = 3


def test_make_example_data_regenerates(tmp_path: Path) -> None:
    """The generator runs clean and produces an xlsx.

    Writes to a tmp path rather than the default (cwd/example_data.xlsx) so
    the committed fixture is never clobbered by a test run.
    """
    out = tmp_path / "example_data.xlsx"
    result = subprocess.run(
        [sys.executable, str(EXAMPLES_DIR / "make_example_data.py"), "--out", str(out)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=300,
    )
    assert result.returncode == 0, f"make_example_data.py failed: {result.stderr}"
    assert out.exists(), "generator did not write the requested --out path"


def test_committed_example_data_exists() -> None:
    """The example workbook is committed, so notebooks/CLI work on a fresh clone."""
    assert EXAMPLE_XLSX.exists(), f"Missing {EXAMPLE_XLSX}"


def test_example_data_has_expected_rows() -> None:
    """The committed workbook has the documented 27-row composition."""
    df = pd.read_excel(EXAMPLE_XLSX)
    assert len(df) == EXPECTED_ROWS

    crm_rows = df[df["sample_tag"].str.startswith("RM")]
    assert len(crm_rows) == EXPECTED_CRM

    # Tags are uppercase (TRIS_1..TRIS_3); the plan's lowercase "tris" matched nothing.
    tris_rows = df[df["sample_tag"].str.upper().str.startswith("TRIS")]
    assert len(tris_rows) == EXPECTED_TRIS

    # Cross-check against the generator's own role column.
    assert (df["crm_or_sample"] == "sample").sum() == 20
    assert (df["crm_or_sample"] == "crm").sum() == EXPECTED_CRM
    assert (df["crm_or_sample"] == "std").sum() == EXPECTED_TRIS
