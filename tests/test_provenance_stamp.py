"""Migration gate: the carbonate provenance stamping helper.

The plan accepted ``returncode in (0, 1, 2)`` for ``--help``, which also passes
when the script crashes on import. The script uses argparse, so ``--help`` must
exit 0 and print its usage.
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "tools" / "stamp_carbonate_provenance.py"


def test_stamp_script_exists() -> None:
    assert SCRIPT.exists(), f"Missing {SCRIPT}"


def test_stamp_script_help_succeeds() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=60,
    )
    assert result.returncode == 0, f"--help failed:\n{result.stderr}"
    assert "usage" in result.stdout.lower()
    assert "--in-place" in result.stdout


def test_stamp_script_errors_on_missing_file(tmp_path: Path) -> None:
    """A missing workbook exits non-zero rather than silently succeeding."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path / "nope.xlsx")],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=60,
    )
    assert result.returncode != 0
    assert "not found" in (result.stdout + result.stderr).lower()


def test_stamp_requires_sample_type_column(tmp_path: Path) -> None:
    """Without sample_type the script cannot tell samples from reference rows."""
    src = tmp_path / "nocol.xlsx"
    pd.DataFrame({"sample_tag": ["S001"], "ta": [2200.0]}).to_excel(src, index=False)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(src)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=120,
    )
    assert result.returncode != 0
    assert "sample_type" in (result.stdout + result.stderr)


def test_stamp_adds_provenance_columns(tmp_path: Path) -> None:
    """Stamping writes *_provenance.xlsx, filling sample rows only.

    Reference rows (crm/std) are deliberately left blank: they carry no
    computed carbonate chemistry.
    """
    src = tmp_path / "book.xlsx"
    pd.DataFrame(
        {
            "sample_tag": ["S001", "S002", "RM213_1"],
            "sample_type": ["sample", "sample", "crm"],
            "ta": [2200.0, 2250.0, 2300.0],
        }
    ).to_excel(src, index=False)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(src)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=120,
    )
    assert result.returncode == 0, f"stamp failed:\n{result.stdout}\n{result.stderr}"

    out = src.with_name("book_provenance.xlsx")
    assert out.exists(), f"expected {out}; stdout:\n{result.stdout}"

    stamped = pd.read_excel(out)
    new_cols = set(stamped.columns) - {"sample_tag", "sample_type", "ta"}
    assert new_cols, "stamping added no columns"
    assert len(stamped) == 3, "stamping changed the row count"

    # Provenance lands on sample rows and is left blank on reference rows.
    col = "carbonate_ph_scale"
    assert col in stamped.columns
    by_tag = stamped.set_index("sample_tag")[col]
    assert by_tag["S001"] == "total"
    assert by_tag["S002"] == "total"
    assert pd.isna(by_tag["RM213_1"]), "CRM row should not be stamped"

    # Pre-existing chemistry survives the read/write round-trip.
    assert stamped["ta"].tolist() == [2200.0, 2250.0, 2300.0]
