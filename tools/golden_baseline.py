#!/usr/bin/env python3
"""Golden baseline of the pipeline's output on the bundled example data.

``tests/golden/example_data/`` holds every ``data/``, ``tables/`` and ``qc/``
CSV that ``run_pipeline.sh examples/example_data.xlsx`` writes (Stages QC to
4), with run-specific columns removed. ``tests/test_golden_baseline.py`` reruns
the pipeline and compares each file, so an engine change that alters output
fails until the baseline is regenerated on purpose.

    pixi run python tools/golden_baseline.py            # regenerate the fixtures
    pixi run python tools/golden_baseline.py --check    # compare without writing

Reports, manifests, logs and figures are not part of the baseline: they carry
timestamps, absolute paths or nondeterministic rendering. See
``tests/golden/README.md`` for the review convention.
"""

from __future__ import annotations

import argparse
import io
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_INPUT = REPO_ROOT / "examples" / "example_data.xlsx"
GOLDEN_DIR = REPO_ROOT / "tests" / "golden" / "example_data"

# Output directories whose CSVs are deliverables; logs/ and reports/ are not.
OUTPUT_SUBDIRS = {"data", "tables", "qc"}

# Columns whose values depend on where and when the run happened: absolute
# input paths (source_file, source_file_stage2, ...) and stage timestamps.
VOLATILE_COLUMN = re.compile(r"^(source_file(_stage\w+)?|stage\w+_processed_utc)$")

# Float comparison tolerance: tight, but allows last-bit differences across
# platforms in PyCO2SYS and NumPy. Applied only in FLOAT_COLUMNS, and only when
# both cells are FLOAT_TEXT; every other cell must match its baseline text.
RTOL = 1e-9
ATOL = 1e-12

# Measured and computed quantities whose last digits may vary by platform. This
# is an allowlist: identifiers (sample, station, batch), flags, counts and text
# are never listed, so they compare exactly even when they look like floats
# (``01.0`` and ``1.0`` are different station IDs). A new float output column
# fails --check on a platform difference until it is added here on purpose.
FLOAT_COLUMNS = frozenset(
    {
        # Stage QC / 1a / 1b: lab measurements and CRM / pH-standard corrections
        "pH_lab", "salinity", "temp_lab", "ta", "ta_certified_umolkg",
        "ta_correction_raw_umolkg", "ta_correction_used_umolkg", "ta_corr_value",
        "ta_corr_sd", "ta_corr_se", "ta_corrected_umolkg", "ta_diff_umolkg",
        "phstd_expected", "phstd_diff", "phstd_correction_raw", "phstd_correction_used",
        "phstd_corr_value", "phstd_corr_sd", "phstd_corr_se", "ph_corrected_from_phstd",
        "ph_after_phstd_qc", "ph_observed", "temperature_measurement_c",
        "overall_correction", "overall_sd",
        # Stage 2 / 3 / 4: field values and carbonate-system results
        "lat", "lon", "latitude_deg", "longitude_deg", "depth_m", "depth_bin_m",
        "depth_round_m", "pressure_output_dbar", "calc_pressure_dbar", "calc_salinity",
        "calc_temperature_c", "temperature_insitu_c", "chlorophyll", "oxygen_umol_l",
        "nitrate_nitrite_umol_l", "phosphate_umol_l", "silicate_umol_l", "ta_umol_kg",
        "ta_best_umolkg", "ph_best", "ph_calculated", "ph_co2sys",
        "ph_best_minus_ph_co2sys", "ph_best_minus_ph_co2sys_temp_harmonized",
        "dic_best_umol_kg", "dic_calculated_umol_kg", "pco2_best_uatm", "pco2_calc_uatm",
        "co2aq_calc_umol_kg", "co3_calc_umol_kg", "hco3_calc_umol_kg",
        "dic_minus_species_sum", "dic_minus_sum", "dic_species_rel_diff",
        "dic_species_sum", "dic_sum_species", "dic_sum_tol", "dic_tol_used",
        # Stage 4 tables: range limits, parsed values and percentages
        "min_allowed", "max_allowed", "value", "pct_missing", "pct_any_carbonate_issue",
        "pct_dic_inconsistent", "pct_ph_diag_mismatch",
    }
)


def output_csvs(out_root: Path) -> list[Path]:
    """Relative paths of every baseline CSV under a pipeline output root."""
    return sorted(
        path.relative_to(out_root)
        for path in out_root.rglob("*.csv")
        if path.parent.name in OUTPUT_SUBDIRS
    )


# A float as the stages write it: has a decimal point or an exponent. Even in a
# FLOAT_COLUMNS column, a value without one (or ``nan``) is compared as text.
FLOAT_TEXT = re.compile(r"^[+-]?(?:(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+)$")


def _parse(text: str) -> pd.DataFrame:
    """Every cell as its CSV text: no type inference and no NA parsing.

    Inference would erase identifier changes (``0213`` reads as ``213``) and NA
    parsing would make a literal ``NA`` equal to an empty cell.
    """
    if not text.strip():  # stages write a bare newline for an empty table
        return pd.DataFrame()
    return pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False, na_filter=False)


def _read(path: Path) -> pd.DataFrame:
    return _parse(path.read_text(encoding="utf-8"))


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Drop run-specific columns, and blank their example values in inventories."""
    out = df.drop(columns=[c for c in df.columns if VOLATILE_COLUMN.match(str(c))])
    if {"column", "example_nonnull"} <= set(out.columns):
        volatile_rows = out["column"].astype(str).str.match(VOLATILE_COLUMN)
        out.loc[volatile_rows, "example_nonnull"] = ""
    return out


def canonical_csv(path: Path) -> str:
    """The normalized CSV text stored in the baseline for one output file."""
    df = normalize(_read(path))
    if df.empty and not len(df.columns):
        return ""  # an empty table; a bare newline would trip end-of-file-fixer
    return df.to_csv(index=False, lineterminator="\n")


def load_canonical(text: str) -> pd.DataFrame:
    """Parse baseline CSV text the same way for fixtures and fresh output."""
    return _parse(text)


def _cells_match(column: str, actual: str, expected: str) -> bool:
    """Exact text, except two floats in a FLOAT_COLUMNS column may differ within tolerance."""
    if actual == expected:
        return True
    if column in FLOAT_COLUMNS and FLOAT_TEXT.match(actual) and FLOAT_TEXT.match(expected):
        return math.isclose(float(actual), float(expected), rel_tol=RTOL, abs_tol=ATOL)
    return False


def compare_frames(actual: pd.DataFrame, expected: pd.DataFrame) -> list[str]:
    """Differences between two text-valued frames, one message per column."""
    if actual.columns.tolist() != expected.columns.tolist():
        return [f"columns differ: {actual.columns.tolist()} != {expected.columns.tolist()}"]
    if len(actual) != len(expected):
        return [f"row count differs: {len(actual)} != {len(expected)}"]
    problems = []
    for col in actual.columns:
        bad = [
            i
            for i, (a, e) in enumerate(zip(actual[col], expected[col], strict=True))
            if not _cells_match(str(col), a, e)
        ]
        if bad:
            i = bad[0]
            problems.append(
                f"column {col!r}: {len(bad)} row(s) differ, first at row {i}: "
                f"{actual[col].iloc[i]!r} != baseline {expected[col].iloc[i]!r}"
            )
    return problems


def run_pipeline(out_root: Path, bash: str = "bash") -> None:
    """Run run_pipeline.sh on the example workbook with default configs."""
    env = os.environ.copy()
    env["PYTHON_BIN"] = sys.executable
    result = subprocess.run(
        [bash, "./run_pipeline.sh", EXAMPLE_INPUT.relative_to(REPO_ROOT).as_posix(), out_root.as_posix()],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"run_pipeline.sh failed with exit {result.returncode}\n"
            f"--- stdout (tail) ---\n{result.stdout[-2000:]}\n"
            f"--- stderr (tail) ---\n{result.stderr[-2000:]}"
        )


def write_baseline(out_root: Path, golden_dir: Path = GOLDEN_DIR) -> list[Path]:
    """Replace the baseline with the normalized CSVs from ``out_root``."""
    if golden_dir.exists():
        shutil.rmtree(golden_dir)
    files = output_csvs(out_root)
    for rel in files:
        target = golden_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(canonical_csv(out_root / rel), encoding="utf-8", newline="\n")
    return files


def compare(out_root: Path, golden_dir: Path = GOLDEN_DIR) -> list[str]:
    """Return one message per difference between ``out_root`` and the baseline."""
    problems: list[str] = []
    fresh = set(output_csvs(out_root))
    golden = set(output_csvs(golden_dir))
    problems += [f"new output not in baseline: {p.as_posix()}" for p in sorted(fresh - golden)]
    problems += [f"baseline output no longer written: {p.as_posix()}" for p in sorted(golden - fresh)]
    for rel in sorted(fresh & golden):
        actual = load_canonical(canonical_csv(out_root / rel))
        expected = load_canonical((golden_dir / rel).read_text(encoding="utf-8"))
        problems += [f"{rel.as_posix()}: {p}" for p in compare_frames(actual, expected)]
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="compare instead of writing")
    parser.add_argument("--bash", default="bash", help="bash executable for run_pipeline.sh")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="roap-golden-") as tmp:
        out_root = Path(tmp) / "out"
        run_pipeline(out_root, bash=args.bash)
        if args.check:
            problems = compare(out_root)
            for problem in problems:
                print(problem)
            print(f"{len(problems)} difference(s) from {GOLDEN_DIR.relative_to(REPO_ROOT)}")
            return 1 if problems else 0
        files = write_baseline(out_root)
    print(f"wrote {len(files)} files to {GOLDEN_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
