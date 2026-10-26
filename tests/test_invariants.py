"""Invariant tests — untouched columns byte-identical per stage (Vector #5)."""

import io
import math
import re
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import pytest


# Stage → target columns mapping (what each stage is ALLOWED to add/modify)
# These are columns the stage *creates or transforms*; everything else must stay identical
STAGE_TARGETS = {
    "02_ta_ph_qc": {
        "ta_corrected_umolkg", "ph_corrected_from_phstd", "ph_after_phstd_qc",
        "ta_correction_applied", "ph_correction_applied",
        "ta_qc_flag", "ph_qc_flag", "ta_crm_status", "ph_std_status",
        "ta_crm_batch", "ta_crm_certified_umolkg", "ta_crm_measured_umolkg",
        "ph_std_type", "ph_std_expected", "ph_std_residual",
    },
    "04_stage1a": {
        "ta_best_umolkg", "ph_best", "ph_co2sys", "pco2_best_uatm",
        "dic_best_umol_kg", "co2aq_calc_umol_kg", "hco3_calc_umol_kg",
        "co3_calc_umol_kg", "omega_aragonite_calc", "omega_calcite_calc",
        "ph_scale_observed_normalized", "ph_scale_calculated_normalized",
        "dic_unit_normalized", "co2aq_unit_normalized", "hco3_unit_normalized",
        "co3_unit_normalized", "carbonate_solver", "carbon_input_pair_used",
        "ta_best_source", "ph_best_source", "ph_co2sys_source",
        "pco2_best_source", "dic_best_source",
        # Canonicalised to "umol kg-1" (schema.normalize_ta_units).
        "ta_units",
    },
    "05_stage1b": {
        "ta_best_umolkg", "ph_best", "ph_co2sys", "pco2_best_uatm",
        "dic_best_umol_kg", "co2aq_calc_umol_kg", "hco3_calc_umol_kg",
        "co3_calc_umol_kg", "omega_aragonite_calc", "omega_calcite_calc",
        "sample_type", "is_sample", "analysis_ready",
        "ta_best_source", "ph_best_source", "ph_co2sys_source",
        "pco2_best_source", "dic_best_source",
        # Reset from stage1b's provenance_defaults.
        "preferred_ta_for_analysis", "preferred_ph_for_analysis",
        "preferred_pco2_for_analysis", "preferred_dic_for_analysis",
        # Recomputed by stage1b's range checks and missing-field flags.
        "flag_ph_co2sys_missing", "flag_ta_units_missing",
        "flag_pressure_output_dbar_missing",
    },
    "06_stage2": {
        "duplicate_flag", "replicate_group", "n_replicates",
        "harmonization_method", "ta_harmonized", "ph_harmonized",
        "pco2_harmonized", "dic_harmonized",
    },
    "07_stage3": {
        "dic_sum", "ph_diagnostic", "ph_diag_harmonized",
        "strict_dic_species_fail", "dic_species_audit",
        "carbonate_solver", "carbon_input_pair_used",
        "carbonate_constants", "carbonate_ph_scale",
        "carbonate_output_temperature",
    },
    "08_stage4": {
        "analysis_audit_status", "audit_flags", "range_flag_count",
        "flag_any_carbonate_issue", "flag_any_carbonate_issue_strict",
        "flag_solver_unknown", "flag_carbon_input_pair_unknown",
        "flag_stage2_replicate_conflict_carried",
        "flag_dic_unit_missing", "flag_dic_inconsistent",
        "flag_dic_inconsistent_robust", "flag_ph_scale_mismatch",
        "flag_ph_best_scale_unexpected", "flag_ph_co2sys_scale_unexpected",
        "flag_ph_diag_mismatch", "flag_ph_diag_mismatch_strict",
        "flag_ph_diag_mismatch_robust", "flag_dic_species_audit_not_run",
        "flag_dic_species_values_missing_audit", "flag_dic_species_audit_strict",
        "flag_dic_species_unit_mismatch_audit", "flag_dic_species_unit_missing_audit",
    },
}


# Where run_pipeline.sh writes each stage's output, relative to the output
# root, and which file it hands to the next stage. 05 writes every row to
# analysis_fields.csv but passes only the sample rows on to 06.
STAGE_OUTPUT = {
    "02_ta_ph_qc": "oa_prelim_data__qc_outputs/sheet_*/data/derived.csv",
    "04_stage1a": "oa_stage1a_outputs/data/staged.csv",
    "05_stage1b": "oa_stage1b_outputs/data/analysis_fields.csv",
    "06_stage2": "oa_stage2_outputs/data/enhanced.csv",
    "07_stage3": "oa_stage3_outputs/data/enhanced.csv",
    "08_stage4": "oa_stage4_outputs/data/analysis_ready.csv",
}
STAGE_INPUT = {
    "02_ta_ph_qc": None,  # the workbook itself
    "04_stage1a": "oa_prelim_data__qc_outputs/sheet_*/data/derived.csv",
    "05_stage1b": "oa_stage1a_outputs/data/staged.csv",
    "06_stage2": "oa_stage1b_outputs/data/analysis_ready_samples.csv",
    "07_stage3": "oa_stage2_outputs/data/enhanced.csv",
    "08_stage4": "oa_stage3_outputs/data/enhanced.csv",
}

EXAMPLE_XLSX = Path("examples/example_data.xlsx")
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
# Re-parsing a float and writing it back can move its last digits.
FLOAT_RTOL = 1e-12


def _read_as_text(path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _workbook_as_text(path: Path) -> pd.DataFrame:
    """The workbook as it would read if written to CSV unchanged."""
    df = pd.read_excel(path)
    return _read_as_text(io.StringIO(df.to_csv(index=False)))


def _same_value(a: str, b: str) -> bool:
    """True if two CSV cells hold the same value.

    Only serialisation differences are allowed: a float written with different
    precision ("1" vs "1.0", last-digit rounding), and a date written in a
    different format for the same instant ("2024-03-01" vs
    "2024-03-01T00:00:00Z"). Case, spelling and any real change in value or
    time are mutations.
    """
    if a == b:
        return True
    try:
        fa, fb = float(a), float(b)
    except ValueError:
        pass
    else:
        if math.isnan(fa) or math.isnan(fb):
            return math.isnan(fa) and math.isnan(fb)
        return math.isclose(fa, fb, rel_tol=FLOAT_RTOL, abs_tol=0.0)
    if _ISO_DATE.match(a) and _ISO_DATE.match(b):
        try:
            ta = pd.Timestamp(a)
            tb = pd.Timestamp(b)
        except ValueError:
            return False
        ta = ta.tz_localize("UTC") if ta.tzinfo is None else ta.tz_convert("UTC")
        tb = tb.tz_localize("UTC") if tb.tzinfo is None else tb.tz_convert("UTC")
        return ta == tb
    return False


def assert_untouched_unchanged(input_df: pd.DataFrame, output_df: pd.DataFrame, target_cols: set, stage_name: str):
    """Assert columns NOT in target_cols keep every value from input to output.

    Both frames must be read as text (see _read_as_text).
    """
    dropped = set(input_df.columns) - set(output_df.columns)
    assert not dropped, f"{stage_name}: Columns dropped: {dropped}"
    assert len(input_df) == len(output_df), (
        f"{stage_name}: row count changed {len(input_df)} -> {len(output_df)}"
    )

    for col in input_df.columns:
        if col in target_cols:
            continue
        for row, (a, b) in enumerate(zip(input_df[col], output_df[col])):
            assert _same_value(a, b), (
                f"{stage_name}: Column '{col}' mutated at row {row}: {a!r} -> {b!r}"
            )


def _one_file(root: Path, pattern: str) -> Path:
    matches = sorted(root.glob(pattern))
    assert len(matches) == 1, f"expected one {pattern} under {root}, found {matches}"
    return matches[0]


@pytest.fixture(scope="module")
def pipeline_run(bash_exe, tmp_path_factory) -> Path:
    """One full run_pipeline.sh run; every stage test reads its files."""
    out = tmp_path_factory.mktemp("invariants") / "outputs"
    result = subprocess.run(
        [bash_exe, "./run_pipeline.sh", EXAMPLE_XLSX.as_posix(), out.as_posix()],
        capture_output=True, text=True, timeout=600,
    )
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"
    return out


@pytest.mark.parametrize("stage_name", list(STAGE_OUTPUT))
def test_stage_invariant_columns(stage_name, pipeline_run):
    """Each stage must not mutate columns outside its declared target set.

    Compares each stage's output against the exact file that stage read.
    """
    if STAGE_INPUT[stage_name] is None:
        input_df = _workbook_as_text(EXAMPLE_XLSX)
    else:
        input_df = _read_as_text(_one_file(pipeline_run, STAGE_INPUT[stage_name]))
    output_df = _read_as_text(_one_file(pipeline_run, STAGE_OUTPUT[stage_name]))

    assert_untouched_unchanged(input_df, output_df, STAGE_TARGETS[stage_name], stage_name)


@pytest.mark.parametrize(
    "before, after",
    [
        ("SAMPLE_A", "sample_a"),  # identifier case
        ("quartz", "quart"),  # trailing character
        ("2024-03-01T00:00:00", "2024-03-01T23:59:59"),  # time of day
        ("2024-03-01", "2024-03-02T00:00:00Z"),  # date
        ("2050.1", "2050.2"),  # numeric value
        ("1", ""),  # value cleared
    ],
)
def test_checker_catches_mutation(before, after):
    """The comparison must fail on a real change in a non-target column."""
    input_df = pd.DataFrame({"record_id": ["x", before]})
    output_df = pd.DataFrame({"record_id": ["x", after]})
    with pytest.raises(AssertionError, match="record_id"):
        assert_untouched_unchanged(input_df, output_df, set(), "synthetic")


@pytest.mark.parametrize(
    "before, after",
    [
        ("1", "1.0"),
        ("0.013999999999999346", "0.0139999999999993"),
        ("2024-03-01", "2024-03-01T00:00:00Z"),
        ("", ""),
    ],
)
def test_checker_allows_serialisation_only(before, after):
    """Re-serialising the same value is not a mutation."""
    input_df = pd.DataFrame({"c": [before]})
    output_df = pd.DataFrame({"c": [after]})
    assert_untouched_unchanged(input_df, output_df, set(), "synthetic")


def test_checker_catches_dropped_column_and_rows():
    df = pd.DataFrame({"a": ["1", "2"], "b": ["3", "4"]})
    with pytest.raises(AssertionError, match="dropped"):
        assert_untouched_unchanged(df, df[["a"]], set(), "synthetic")
    with pytest.raises(AssertionError, match="row count"):
        assert_untouched_unchanged(df, df.iloc[:1], set(), "synthetic")


def test_lat_lon_never_mutated(bash_exe):
    """Specific regression test for the lat/lon overwrite bug (Vector #5)."""
    input_path = Path("examples/example_data.xlsx")
    input_df = pd.read_excel(input_path)

    # Ensure lat/lon exist in example data
    assert "latitude_deg" in input_df.columns
    assert "longitude_deg" in input_df.columns

    # Run full pipeline via run_pipeline.sh
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "outputs"
        result = subprocess.run(
            [bash_exe, "./run_pipeline.sh", input_path.as_posix(), output_dir.as_posix()],
            capture_output=True, text=True, timeout=300
        )
        assert result.returncode == 0, f"Pipeline failed: {result.stderr}"

        final_csv = output_dir / "oa_stage4_outputs" / "data" / "analysis_ready.csv"
        assert final_csv.exists(), "Final output not found"
        final_df = pd.read_csv(final_csv)

    # lat/lon must be byte-identical
    for col in ["latitude_deg", "longitude_deg"]:
        pd.testing.assert_series_equal(
            input_df[col], final_df[col],
            check_names=False,
            check_exact=True,
            obj=f"CRITICAL: '{col}' mutated by pipeline (Vector #5)"
        )


def test_provenance_columns_never_mutated(bash_exe):
    """Provenance columns must not be silently overwritten."""
    input_path = Path("examples/example_data.xlsx")
    input_df = pd.read_excel(input_path)

    provenance_cols = ["carbonate_solver", "carbon_input_pair_used",
                       "carbonate_constants", "carbonate_ph_scale",
                       "carbonate_output_temperature"]
    existing_prov = [c for c in provenance_cols if c in input_df.columns]

    if not existing_prov:
        pytest.skip("No provenance columns in input data")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "outputs"
        result = subprocess.run(
            [bash_exe, "./run_pipeline.sh", input_path.as_posix(), output_dir.as_posix()],
            capture_output=True, text=True, timeout=300
        )
        assert result.returncode == 0

        final_csv = output_dir / "oa_stage4_outputs" / "data" / "analysis_ready.csv"
        final_df = pd.read_csv(final_csv)

    for col in existing_prov:
        pd.testing.assert_series_equal(
            input_df[col], final_df[col],
            check_names=False,
            check_exact=True,
            obj=f"Provenance column '{col}' mutated"
        )
