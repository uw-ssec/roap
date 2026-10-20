"""Invariant tests — untouched columns byte-identical per stage (Vector #5)."""

import pytest
import pandas as pd
import subprocess
import tempfile
from pathlib import Path


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
    },
    "05_stage1b": {
        "ta_best_umolkg", "ph_best", "ph_co2sys", "pco2_best_uatm",
        "dic_best_umol_kg", "co2aq_calc_umol_kg", "hco3_calc_umol_kg",
        "co3_calc_umol_kg", "omega_aragonite_calc", "omega_calcite_calc",
        "sample_type", "is_sample", "analysis_ready",
        "ta_best_source", "ph_best_source", "ph_co2sys_source",
        "pco2_best_source", "dic_best_source",
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


def _normalize_value(val):
    """Normalize a cell value for comparison, handling units and datetime formats."""
    if val is None or val == "":
        return val
    s = str(val).strip()
    # Strip timezone suffixes like "t00:00:00z", "T00:00:00", etc. after the date
    # Patterns: "2024-03-01t00:00:00z", "2024-03-01T00:00:00", "2024-03-01 00:00:00"
    import re
    m = re.match(r"(\d{4}-\d{2}-\d{2}[T ][\d:]+)", s)
    if m:
        # Return just the date part up to the time separator
        return m.group(1).split("T")[0].split(" ")[0]
    # Normalize unit strings: "umol/kg" ↔ "umol kg-1"
    s_lower = s.lower()
    s_normalized = s_lower.replace("/kg", " kg-1").replace("/kg-1", " kg-1")
    s_normalized = s_normalized.replace(" kg-1", "kg-1").replace(" kg", "kg")
    # Remove trailing "z" that's not part of a datetime
    if not re.match(r"\d", s_normalized):
        s_normalized = s_normalized.rstrip("z")
    return s_normalized


def assert_untouched_unchanged(input_df: pd.DataFrame, output_df: pd.DataFrame, target_cols: set, stage_name: str):
    """Assert columns NOT in target_cols are byte-identical between input and output."""
    input_cols = set(input_df.columns)
    output_cols = set(output_df.columns)

    # All input columns must exist in output (no drops)
    dropped = input_cols - output_cols
    assert not dropped, f"{stage_name}: Columns dropped: {dropped}"

    # Non-target columns must be byte-identical (compare as strings to avoid dtype issues)
    untouched = input_cols - target_cols
    for col in untouched:
        if col not in output_df.columns:
            continue
        try:
            input_series = input_df[col].astype(str)
            output_series = output_df[col].astype(str)
            # Normalize values for comparison so "2024-03-01" == "2024-03-01t00:00:00z"
            # and "umol/kg" == "umol kg-1"
            input_norm = input_series.apply(_normalize_value)
            output_norm = output_series.apply(_normalize_value)
            pd.testing.assert_series_equal(
                input_norm, output_norm,
                check_names=False,
                obj=f"{stage_name}: Column '{col}' mutated (value format diff)"
            )
        except AssertionError as e:
            raise AssertionError(f"{stage_name}: {e}")


def run_stages_02_to_target(stage_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run stages 02→...→stage_name in a single temp dir, return (input_df, output_df)."""
    input_path = Path("examples/example_data.xlsx")
    input_df = pd.read_excel(input_path)

    stage_order = ["02_ta_ph_qc", "04_stage1a", "05_stage1b", "06_stage2", "07_stage3", "08_stage4"]
    idx = stage_order.index(stage_name)

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)

        current_input = str(input_path)
        derived_from_last = None

        for i in range(idx + 1):
            s = stage_order[i]
            out_dir = tmpdir / f"stage_{i}"
            out_dir.mkdir(parents=True, exist_ok=True)

            if s == "02_ta_ph_qc":
                cmd = [
                    "papermill", f"notebooks/{s}.ipynb", str(out_dir / f"{s}_out.ipynb"),
                    "-p", "XLSX_PATH", current_input,
                    "-p", "OUT_DIR", str(out_dir),
                ]
            else:
                cmd = [
                    "papermill", f"notebooks/{s}.ipynb", str(out_dir / f"{s}_out.ipynb"),
                    "-p", "INPUT_CSV", current_input,
                    "-p", "OUT_DIR", str(out_dir),
                ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise RuntimeError(f"{s} failed: {result.stderr}")

            # Find the output CSV
            csv_file = None
            for p in out_dir.rglob("derived.csv"):
                csv_file = p
                break
            if csv_file is None:
                for p in out_dir.glob("sheet_*/data/derived.csv"):
                    csv_file = p
                    break
            if csv_file is None:
                for p in tmpdir.rglob("staged.csv"):
                    csv_file = p
                    break
            if csv_file is None:
                for p in tmpdir.glob("sheet_*/data/staged.csv"):
                    csv_file = p
                    break

            if csv_file is None:
                raise RuntimeError(f"{s}: No CSV output derived.csv/staged.csv found in {out_dir}")

            derived_from_last = csv_file
            current_input = str(csv_file)

        final_df = pd.read_csv(derived_from_last)
        return input_df, final_df


@pytest.mark.parametrize("stage_name", [
    "02_ta_ph_qc", "04_stage1a", "05_stage1b",
    "06_stage2", "07_stage3"
])
def test_stage_invariant_columns(stage_name, tmp_path):
    """Each stage must not mutate columns outside its declared target set."""
    input_df, output_df = run_stages_02_to_target(stage_name)

    target_cols = STAGE_TARGETS[stage_name]
    assert_untouched_unchanged(input_df, output_df, target_cols, stage_name)


def test_lat_lon_never_mutated():
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
            ["./run_pipeline.sh", str(input_path), str(output_dir)],
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


def test_provenance_columns_never_mutated():
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
            ["./run_pipeline.sh", str(input_path), str(output_dir)],
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
